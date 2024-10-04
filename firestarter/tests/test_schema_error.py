from firestarter.common.validations import validate_config
from jsonschema.exceptions import SchemaError
import pytest
import os

VALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images.yaml')

INVALID_SCHEMA_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/invalid_jsonschema.json')


def test_schema_error() -> None:
    with pytest.raises(SchemaError):
        validate_config(VALID_CONFIG_FILE_PATH, INVALID_SCHEMA_FILE_PATH)
