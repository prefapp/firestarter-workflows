from firestarter.workflows.ci.dagger_context import Context
from firestarter.workflows.ci.task_manager import TaskManager
import anyio
import os
import dagger
import pytest
from firestarter.workflows.ci.bash_runner import exec_run_in_container


def test_dagger_workflow() -> None:

    async def myTestFunc(context: Context) -> None:
        tm: TaskManager = TaskManager()
        tm.context = context
        tm.load(
            os.path.join(
                os.path.dirname(__file__), 'fixtures/test_workflow.yaml',
            ),
            '../workflows/ci/schema.json',
        )
        await tm.run()

    anyio.run(lambda: Context().start(myTestFunc))


@pytest.mark.asyncio
async def test_bash_runner_stops_on_failed_command():
    async with dagger.Connection() as client:
        container = client.container().from_("node:20-slim")
        result = await exec_run_in_container(
            'false\necho "should not run"', container, client
        )

        with pytest.raises(dagger.ExecError) as error:
            await result.stdout()

        assert error.value.exit_code == 1
        assert "should not run" not in error.value.stdout


@pytest.mark.asyncio
async def test_dockerfile_build_and_export(tmp_path):
    (tmp_path / "Dockerfile").write_text(
        "FROM alpine:3.21\n"
        "ARG MESSAGE\n"
        "RUN --mount=type=secret,id=build_secret "
        'test "$(cat /run/secrets/build_secret)" = "secret-value" '
        '&& echo "$MESSAGE" > /message\n'
    )
    archive = tmp_path / "image.tar"

    async with dagger.Connection() as client:
        container = client.host().directory(str(tmp_path)).docker_build(
            platform=dagger.Platform("linux/amd64"),
            build_args=[dagger.BuildArg(name="MESSAGE", value="hello")],
            secrets=[client.set_secret("build_secret", "secret-value")],
        ).with_label("source.code.revision", "test-revision")

        assert await container.file("/message").contents() == "hello\n"
        assert await container.label("source.code.revision") == "test-revision"
        await container.export(str(archive))

    assert archive.stat().st_size > 0
