from firestarter.common.validations import validate_config
from jsonschema.exceptions import ValidationError, SchemaError
import pytest
from unittest import TestCase
from ruamel.yaml import YAML
import os

VALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images.yaml')

INVALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images_ko.yaml')

SCHEMA_FILE_PATH: str = '../workflows/build_images/resources/schema.json'

INVALID_SCHEMA_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/invalid_jsonschema.json')

yaml=YAML(typ='safe')

# if the config file is valid, the function returns the config data
def test_validate_schema() -> None:
    with open(VALID_CONFIG_FILE_PATH, 'r') as config_file:
        config_data: dict = yaml.load(config_file)
        TestCase().assertDictEqual(validate_config(VALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH), config_data)

# if the config file is invalid, a ValidationError exception is raised
def test_validate_schema_error() -> None:
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

# if the config file does not exist, a FileNotFoundError exception is raised
def test_validation_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        validate_config("/tmp/fake_build_images.yaml", SCHEMA_FILE_PATH)

# if the schema file is incorrect, a SchemaError exception is raised
def test_schema_error() -> None:
    with pytest.raises(SchemaError):
        validate_config(VALID_CONFIG_FILE_PATH, INVALID_SCHEMA_FILE_PATH)


@pytest.mark.parametrize('image_type', ['snapshots', 'releases'])
@pytest.mark.parametrize('registry_field', ['registry', 'extra_registries'])
@pytest.mark.parametrize('auth_strategy', [
    'azure_oidc', 'aws_oidc', 'generic', 'ghcr', 'dockerhub',
])
def test_validate_registry_auth_strategy(tmp_path, image_type, registry_field, auth_strategy) -> None:
    registry = {
        'name': 'test-validacion',
        'repository': 'test',
        'auth_strategy': auth_strategy,
    }
    config_data = {image_type: {'default': {
        'dockerfile': 'Dockerfile',
        registry_field: [registry] if registry_field == 'extra_registries' else registry,
    }}}
    config_path = tmp_path / 'build_images.yaml'
    with config_path.open('w') as config_file:
        yaml.dump(config_data, config_file)

    assert validate_config(str(config_path), SCHEMA_FILE_PATH) == config_data


@pytest.mark.parametrize('image_type', ['snapshots', 'releases'])
@pytest.mark.parametrize('registry_field', ['registry', 'extra_registries'])
def test_validate_unknown_registry_auth_strategy(tmp_path, image_type, registry_field) -> None:
    registry = {
        'name': 'test-validacion',
        'repository': 'test',
        'auth_strategy': 'unknown',
    }
    config_data = {image_type: {'default': {
        'dockerfile': 'Dockerfile',
        registry_field: [registry] if registry_field == 'extra_registries' else registry,
    }}}
    config_path = tmp_path / 'build_images.yaml'
    with config_path.open('w') as config_file:
        yaml.dump(config_data, config_file)

    with pytest.raises(ValidationError, match="'unknown' is not one of"):
        validate_config(str(config_path), SCHEMA_FILE_PATH)
