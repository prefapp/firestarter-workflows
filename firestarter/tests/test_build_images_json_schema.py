from firestarter.common.validations import validate_config
from firestarter.workflows.ci.task_manager import TaskManager
from jsonschema.exceptions import ValidationError, SchemaError
import pytest
import os

VALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images.yaml')

INVALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images_ko.yaml')

SCHEMA_FILE_PATH: str = '../workflows/build_images/resources/schema.json'

INVALID_SCHEMA_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/invalid_jsonschema.json')

def test_validate_schema() -> None:
    try:
        validate_config(VALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)
    except FileNotFoundError as fnf_error:
        pytest.fail(f"File not found: {fnf_error.filename}")


def test_validate_schema_error() -> None:
    with pytest.raises(ValidationError, match="Additional properties are not allowed"):
        try:
            validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)
        except FileNotFoundError as fnf_error:
            pytest.fail(f"File not found: {fnf_error.filename}")

def test_validation_error_message() -> None:
    with pytest.raises(ValidationError):
        validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

def test_schema_error() -> None:
    with pytest.raises(SchemaError):
        validate_config(VALID_CONFIG_FILE_PATH, INVALID_SCHEMA_FILE_PATH)
