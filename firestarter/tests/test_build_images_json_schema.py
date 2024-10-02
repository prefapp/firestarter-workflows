from firestarter.common.validations import validate_config
from firestarter.workflows.ci.task_manager import TaskManager
from jsonschema.exceptions import ValidationError
import pytest
import os

VALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/flavors.yaml')

INVALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/flavors_error.yaml')

SCHEMA_FILE_PATH: str = '../workflows/build_images/resources/schema.json'

def test_validate_schema() -> None:
    validate_config(VALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

def test_validate_schema_error() -> None:
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)