from firestarter.workflows.build_images.build_images import BuildImages
from firestarter.workflows.build_images.config import Image
import pytest
from unittest import TestCase
from ruamel.yaml import YAML
import subprocess
from mock_classes import DaggerContextMock
import os

yaml = YAML(typ='safe')

vars = {
    "from": "aaaaaaa",
    "repo_name": "test_repo_name",
    "snapshots_registry": "test_snapshots",
    "releases_registry": "test_releases",
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

# The BuildImages object is correctly created
def test_build_images_object_creation() -> None:
    global builder
    builder = BuildImages(
        vars=vars, secrets=secrets, config_file=config_file_path
    )

    assert builder.from_version == vars["from"]
    assert builder.repo_name == vars["repo_name"]
    assert builder.snapshots_registry == vars["snapshots_registry"]
    assert builder.releases_registry == vars["releases_registry"]


# The object correctly returns the flavor data of a chosen flavor,
# as written in fixtures/build_images.yaml
def test_get_flavor_data() -> None:
    chosen_flavor = "flavor1"
    registry, full_repo_name, build_args, dockerfile, extra_registries =\
            builder.get_flavor_data(chosen_flavor)

    assert registry == vars["snapshots_registry"]
    assert full_repo_name == vars["repo_name"]
    assert build_args == config_data["snapshots"][chosen_flavor]["build_args"]
    assert dockerfile == config_data["snapshots"][chosen_flavor]["dockerfile"]
    assert extra_registries == config_data["snapshots"][chosen_flavor]["extra_registries"]

    chosen_flavor = "flavor3"
    registry, full_repo_name, build_args, dockerfile, extra_registries =\
            builder.get_flavor_data(chosen_flavor)

    assert registry == config_data["snapshots"][chosen_flavor]["registry"]["name"]
    assert full_repo_name == config_data["snapshots"][chosen_flavor]["registry"]["repository"]
    assert build_args == config_data["snapshots"][chosen_flavor]["build_args"]
    assert dockerfile == config_data["snapshots"][chosen_flavor]["dockerfile"]
    assert extra_registries == config_data["snapshots"][chosen_flavor]["extra_registries"]


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


# The object correctly filters flavors and returns only those where autobuild = true
def test_filter_auto_build() -> None:
    builder.filter_auto_build()

    assert len(builder.flavors) == 1
    assert builder.flavors[0] == "flavor3"


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

    subprocess_mock_return_value = completed_process_mock(
        args=None, returncode=0
    )
    subprocess_mock_return_value.stdout = TAG_INPUT.encode("windows-1252")

    # Test tag input
    subprocess_mock = subprocess
    subprocess_mock.run = mocker.MagicMock(
        name="subprocess.run.mock",
        return_value=subprocess_mock_return_value
    )

    tag_input_dereference = builder.dereference_from_input(TAG_INPUT)

    assert tag_input_dereference == TAG_INPUT

    # Test long sha input
    long_sha_input_dereference = builder.dereference_from_input(LONG_SHA_INPUT)

    assert long_sha_input_dereference == SHORT_SHA_INPUT

    # Test long sha input
    short_sha_input_dereference = builder.dereference_from_input(SHORT_SHA_INPUT)

    assert short_sha_input_dereference == SHORT_SHA_INPUT

@pytest.mark.asyncio
async def test_test_image(mocker) -> None:
    mocker.patch("docker.DockerClient")
    mocker.return_value = None
    mocker.patch.object(os, "remove")
    mocker.return_value = True
    mocker.patch("builtins.open")
    mocker.return_value = ""

    # Correct call, doesn't raise any errors
    await builder.test_image(DaggerContextMock())
