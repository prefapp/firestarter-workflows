from firestarter.workflows.build_images.build_images import BuildImages
from firestarter.workflows.build_images.config import Image
import pytest
from unittest.mock import patch
from ruamel.yaml import YAML
import subprocess
from mock_classes import DaggerContextMock, DaggerImageMock
import os
import docker
import json
import requests
import uuid
import dagger

yaml = YAML(typ='safe')

vars = {
    "from": "aaaaaaa",
    "repo_name": "xxx/yyy",
    "snapshots_registry": "xxxx.azurecr.io",
    "releases_registry": "xxxx.azurecr.io",
    "snapshots_registry_creds": "test_snapshots_creds",
    "releases_registry_creds": "test_releases_creds",
}
secrets = {}
config_file_path = "./fixtures/build_images.yaml"

with open(config_file_path, 'r') as config_file:
    config_data = yaml.load(config_file.read())

test_flavor = Image.from_dict({
    "auto": False,
    "build_always": False,
    "registry": {
        "name": "test_registry",
        "repository": "test_repository",
        "auth_strategy": "test_auth",
        "creds": "test_creds",
    },
    "extra_registries": {},
    "build_args": {},
    "secrets": {},
    "dockerfile": ""
})

builder = None


@pytest.fixture(autouse=True)
def reset_builder_value() -> None:
    global builder

    builder = BuildImages(
        vars=vars, secrets=secrets, config_file=config_file_path
    )


# The BuildImages object is correctly created
def test_build_images_constructor() -> None:
    assert builder.from_version == vars["from"]
    assert builder.repo_name == vars["repo_name"]
    assert builder.snapshots_registry == vars["snapshots_registry"]
    assert builder.releases_registry == vars["releases_registry"]


# The object correctly calls the git command
def test_checkout_git_repository(mocker) -> None:
    mocker.patch("subprocess.run")
    builder.checkout_git_repository("test_repo")

    subprocess.run.assert_called_once_with(["git", "checkout", "test_repo"])


# A git reference is correctly dereference into a tag/short sha
def test_dereference_from_input(mocker) -> None:
    TAG_INPUT = "test_tag"
    LONG_SHA_INPUT = "6a323778def4145d533dacafe003abb8df5bd5e0"
    SHORT_SHA_INPUT = "6a32377"
    BRANCH_INPUT = "test_branch"

    completed_process_mock = subprocess.CompletedProcess
    completed_process_mock.check_return_code = mocker.MagicMock(
        name="completed_process.check_return_code.mock",
        return_value=True
    )

    subprocess_mock_tag_return_value = completed_process_mock(
        args=None, returncode=0
    )
    subprocess_mock_tag_return_value.stdout = TAG_INPUT.encode("windows-1252")

    subprocess_mock_empty_return_value = completed_process_mock(
        args=None, returncode=0
    )
    subprocess_mock_empty_return_value.stdout = "".encode("windows-1252")

    subprocess_mock_sha_return_value = completed_process_mock(
        args=None, returncode=0
    )
    subprocess_mock_sha_return_value.stdout = LONG_SHA_INPUT.encode(
        "windows-1252"
    )

    # Test tag input
    subprocess_mock = subprocess
    subprocess_mock.run = mocker.MagicMock(
        name="subprocess.run.mock",
        side_effect=[
            subprocess_mock_tag_return_value,
            subprocess_mock_empty_return_value,
            subprocess_mock_sha_return_value,
        ]
    )

    tag_input_dereference = builder.dereference_from_input(TAG_INPUT)

    assert tag_input_dereference == TAG_INPUT

    # Test long sha input
    long_sha_input_dereference = builder.dereference_from_input(LONG_SHA_INPUT)

    assert long_sha_input_dereference == SHORT_SHA_INPUT

    # Test short sha input
    short_sha_input_dereference = builder.dereference_from_input(SHORT_SHA_INPUT)

    assert short_sha_input_dereference == SHORT_SHA_INPUT

    # Test branch input
    branch_input_dereference = builder.dereference_from_input(BRANCH_INPUT)

    assert branch_input_dereference == SHORT_SHA_INPUT


# TODO
def test_resolve_secrets() -> None:
    pass


# TODO
def test_filter_flavors() -> None:
    pass


# The object correctly filters flavors and returns only those where autobuild = true
def test_filter_auto_build() -> None:
    builder.filter_auto_build()

    assert len(builder.flavors) == 1
    assert builder.flavors[0] == "flavor3"


# The object correctly tests an image is valid
@pytest.mark.asyncio
async def test_test_image(mocker) -> None:
    CONTAINERS_RUN_RETURN_VALUE = "test-output-containers"

    docker_api_mock = docker.api.client.APIClient
    docker_api_mock._retrieve_server_version = mocker.MagicMock(
        name="docker.api.client.APIClient._retrieve_server_version.mock",
        return_value="v2"
    )

    json_mock = json
    json_mock.load = mocker.MagicMock(
        name="json.load.mock",
        return_value={"proxies": {}}
    )

    requests_mock = requests.adapters
    requests_mock.send = mocker.MagicMock(
        name="requests.send.mock",
        return_value=True
    )

    mocker.patch("docker.DockerClient")

    docker_client_mock = docker.DockerClient
    docker_client_mock().images.load = mocker.MagicMock(
        name="docker.DockerClient.images.load.mock",
        return_value=[DaggerImageMock("123456789")]
    )
    docker_client_mock().containers.run = mocker.MagicMock(
        name="docker.DockerClient.containers.run.mock",
        return_value=CONTAINERS_RUN_RETURN_VALUE.encode("windows-1252")
    )

    mocker.patch.object(os, "remove")
    os_remove_mock = os.remove
    os_remove_mock.return_value = True
    mocker.patch("builtins.open")
    mocker.return_value = ""

    uuid_mock = uuid
    uuid_mock.uuid4 = mocker.MagicMock(
        name="uuid.uuid4.mock",
        side_effect=["correct_call", "container_error", "generic_error"]
    )

    # Correct call, doesn't raise any errors
    correct_result = await builder.test_image(DaggerContextMock())

    assert correct_result == CONTAINERS_RUN_RETURN_VALUE
    os_remove_mock.assert_called_with("correct_call.tar")

    # Incorrect call, raises ContainerError
    with pytest.raises(Exception, match="Structure test failed."):
        incorrect_result = await builder.test_image(DaggerContextMock(True))

    os_remove_mock.assert_called_with("container_error.tar")

    # Incorrect call, raises generic error
    with pytest.raises(Exception, match="Mock error generic"):
        incorrect_result = await builder.test_image(DaggerContextMock(False, True))

    os_remove_mock.assert_called_with("generic_error.tar")


# The object can correctly compile and publish an image
@pytest.mark.asyncio
async def test_compile_image_and_publish(mocker) -> None:
    async def call_and_test_compile_image_and_publish(
        mocker, publish: bool, container_structure_filename: str
    ) -> None:
        ciap_vars = vars.copy()
        ciap_vars["publish"] = publish
        ciap_vars["container_structure_filename"] = container_structure_filename
        ciap_builder = BuildImages(
            vars=ciap_vars, secrets={}, config_file=config_file_path
        )

        build_args = { "test_arg": "a" }
        secrets = { "test_secret": "b" }
        dockerfile = "/path/to/dockerfile"
        image = "image_tag"

        mocker.patch.object(ciap_builder, "test_image")
        ciap_builder_test_image_mock = ciap_builder.test_image
        ciap_builder_test_image_mock.return_value = "Mock test image result"

        ctx_mock = DaggerContextMock()
        mocker.patch.object(ctx_mock, "publish")
        ctx_mock_publish_mock = ctx_mock.publish

        await ciap_builder.compile_image_and_publish(
            ctx_mock, build_args, secrets, dockerfile, image
        )

        if publish:
            ctx_mock_publish_mock.assert_called_with(address=f"{image}")
        else:
            ctx_mock_publish_mock.assert_not_called()

        if container_structure_filename is not None:
            ciap_builder_test_image_mock.assert_called_with(ctx_mock)
        else:
            ciap_builder_test_image_mock.assert_not_called()

        assert ctx_mock.build_args == build_args
        assert ctx_mock.secrets == secrets
        assert ctx_mock.dockerfile == dockerfile

        assert ctx_mock.label_list["source.code.revision"] == builder.from_version
        assert ctx_mock.label_list["repository.name"] == builder.repo_name


    # builder.publish is True and builder.container_structure_filename has no value
    await call_and_test_compile_image_and_publish(mocker, True, None)

    # builder.publish is False and builder.container_structure_filename has value
    await call_and_test_compile_image_and_publish(mocker, False, "filename")

    # builder.publish is True and builder.container_structure_filename has value
    await call_and_test_compile_image_and_publish(mocker, True, "another_filename")

    # builder.publish is Falsee and builder.container_structure_filename has no value
    await call_and_test_compile_image_and_publish(mocker, False, None)


@pytest.mark.asyncio
async def test_compile_images_for_all_flavors(mocker) -> None:
    mocker.patch("dagger.Config")
    mocker.patch("dagger.Connection")
    mocker.patch.object(builder, "compile_image_and_publish")

    dagger_config_mock = dagger.Config
    dagger_connection_mock = dagger.Connection
    builder_compile_image_and_publish_mock = builder.compile_image_and_publish

    builder._flavors = "flavor1, flavor3"
    builder.filter_flavors()

    result = await builder.compile_images_for_all_flavors()

    assert len(result) == 4
    assert result[0]["flavor"] == "flavor1"
    assert result[0]["repository"] == "xxx/yyy"
    assert result[1]["flavor"] == "flavor1"
    assert result[1]["repository"] == "repo1"
    assert result[2]["flavor"] == "flavor3"
    assert result[2]["repository"] == "repository3"
    assert result[3]["flavor"] == "flavor3"
    assert result[3]["repository"] == "repo3"


# The object correctly returns the flavor data of a chosen flavor,
# as written in fixtures/build_images.yaml
def test_get_flavor_data() -> None:
    flavor_list = ["flavor1", "flavor3"]

    for flavor in flavor_list:
        registry, full_repo_name, build_args, dockerfile, extra_registries =\
                builder.get_flavor_data(flavor)

        assert registry == config_data["snapshots"][flavor]["registry"]["name"]
        assert full_repo_name == config_data["snapshots"][flavor]["registry"]["repository"]
        assert build_args == config_data["snapshots"][flavor]["build_args"]
        assert dockerfile == config_data["snapshots"][flavor]["dockerfile"]
        assert extra_registries == config_data["snapshots"][flavor]["extra_registries"]


# The object gets the registry data correctly
def test_get_flavor_registry_data() -> None:
    data = builder.get_flavor_registry_data(test_flavor)

    assert data["name"] == test_flavor.registry["name"]
    assert data["full_repo_name"] == test_flavor.registry["repository"]
    assert data["auth_strategy"] == test_flavor.registry["auth_strategy"]
    assert data["creds"] == test_flavor.registry["creds"]


# The object correctly detects if its flavors should be autobuilding
def test_is_autobuild() -> None:
    shouldnt_be = builder.is_auto_build()

    assert shouldnt_be == False

    previous_flavors = builder.flavors
    builder._flavors = None
    should_be = builder.is_auto_build()

    assert should_be == True

    builder._flavors = previous_flavors

# TODO
def test_login() -> None:
    pass
