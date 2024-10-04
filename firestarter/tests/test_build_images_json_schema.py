from firestarter.common.validations import validate_config
from firestarter.workflows.ci.task_manager import TaskManager
from jsonschema.exceptions import ValidationError, SchemaError
import pytest
from unittest import TestCase
import yaml
import os

VALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images.yaml')

INVALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images_ko.yaml')

SCHEMA_FILE_PATH: str = '../workflows/build_images/resources/schema.json'

INVALID_SCHEMA_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/invalid_jsonschema.json')

def test_validate_schema() -> None:
    with open(VALID_CONFIG_FILE_PATH, 'r') as config_file:
        config_data: dict = yaml.safe_load(config_file)
        TestCase().assertDictEqual(validate_config(VALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH), config_data)

def test_validate_schema_error() -> None:
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

def test_validation_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        validate_config("/tmp/fake_build_images.yaml", SCHEMA_FILE_PATH)

def test_schema_error() -> None:
    with pytest.raises(SchemaError):
        validate_config(VALID_CONFIG_FILE_PATH, INVALID_SCHEMA_FILE_PATH)
