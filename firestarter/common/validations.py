from jsonschema import validate
from .preprocessor import PreProcessor
from string import Template
import os
import json
import yaml


def process_context_var(context: dict, var_name: str, context_name: str) -> str:
    if var_name not in context.keys():
        raise ValueError(
            f"{var_name} could not be found in the {context_name} context"
        )

    return context[var_name]

def process_env_var(var_name: str) -> str:
    if var_name not in os.environ.keys():
        raise ValueError(f"{var_name} could not be found in the ENV context")

    return os.environ[var_name]

def helper_get_config_schema(schema_path: str) -> dict:
    CONFIG_SCHEMA = False

    with open(os.path.join(os.path.dirname(__file__), schema_path)) as schema:
        CONFIG_SCHEMA = json.load(schema)

    return CONFIG_SCHEMA


def validate_config(config_path: str, schema_path: str, context = None) -> dict:
    with open(config_path, 'r') as config_file:
        if context:
            config_tpl: Template = Template(config_file.read())
            config_str: str = config_tpl.safe_substitute(context.vars_context)
        else:
            config_str: str = config_file.read()

        config_data: dict = yaml.safe_load(config_str)

        validate(
            instance=config_data,
            schema=helper_get_config_schema(schema_path),
        )

        return config_data
