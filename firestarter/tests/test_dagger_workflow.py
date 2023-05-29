from firestarter.workflows.ci.dagger_context import Context
from firestarter.workflows.ci.task_manager import TaskManager
import anyio
import os


def test_dagger_workflow() -> None:

    def myTestFunc(context: Context) -> None:
        tm: TaskManager = TaskManager()
        tm.context = context
        tm.load(
            os.path.join(
                os.path.dirname(__file__), 'fixtures/test_workflow.yaml',
            ),
            '../workflows/ci/schema.json',
        )
        tm.run()

    anyio.run(lambda: Context().start(myTestFunc))

