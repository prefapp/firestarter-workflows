from firestarter.workflows.build_images.build_images import BuildImages
from firestarter.workflows.build_images.config import Image
import pytest
from unittest import TestCase
import yaml
import os

vars = {
    "from": "aaaaaaa",
    "repo_name": "test_repo_name",
    "snapshots_registry": "test_snapshots",
    "releases_registry": "test_releases",
    "snapshots_registry_creds": "test_snapshots_creds",
    "releases_registry_creds": "test_releases_creds",
}
secrets = {}
config_file = "fixtures/build_images.yaml"
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

# Check the BuildImages object is correctly created
def test_build_images_object_creation() -> None:
    builder = BuildImages(
        vars=vars, secrets=secrets, config_file=config_file
    )
    assert builder.from_version == vars["from"]
    assert builder.repo_name == vars["repo_name"]
    assert builder.snapshots_registry == vars["snapshots_registry"]
    assert builder.releases_registry == vars["releases_registry"]

    data = builder.get_flavor_registry_data(test_flavor)

    assert data["name"] == test_flavor.registry["name"]
    assert data["full_repo_name"] == test_flavor.registry["repository"]
    assert data["auth_strategy"] == test_flavor.registry["auth_strategy"]
    assert data["creds"] == test_flavor.registry["creds"]
