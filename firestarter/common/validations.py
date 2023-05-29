from jsonschema import validate
from .preprocessor import PreProcessor
import os
import json
import yaml


def helper_get_config_schema(schema_path: str) -> dict:
    CONFIG_SCHEMA = False

    with open(os.path.join(os.path.dirname(__file__), schema_path)) as schema:
        CONFIG_SCHEMA = json.load(schema)

    return CONFIG_SCHEMA


def validate_config(config_path: str, schema_path: str, context = None) -> dict:
    with open(config_path, 'r') as config_file:
        if context:
            preprocessor: PreProcessor = PreProcessor(config_file.read())
            config_str: str = preprocessor.preprocess({
                "vars": lambda v: context.vars[v],
                "secrets": lambda s: context.secrets[s],
                "env": lambda e: os.environ[e],
            })
        else:
            config_str: str = config_file.read()

        config_data: dict = yaml.load(config_str, Loader=yaml.Loader)

        validate(
            instance=config_data,
            schema=helper_get_config_schema(schema_path),
        )

        return config_data
