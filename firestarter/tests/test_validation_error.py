from firestarter.common.validations import validate_config
from jsonschema.exceptions import ValidationError
import pytest
import os

# Definir las rutas de los archivos de prueba
INVALID_CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/build_images_ko.yaml')

SCHEMA_FILE_PATH: str = '../workflows/build_images/resources/schema.json'


def test_validation_error_message() -> None:
    with pytest.raises(ValidationError):
        validate_config(INVALID_CONFIG_FILE_PATH, SCHEMA_FILE_PATH)
