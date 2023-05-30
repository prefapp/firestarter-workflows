from jsonschema import validate
from .preprocessor import PreProcessor
import os
import json
import yaml


def process_var(context, var_name: str) -> str:
    if var_name not in context.vars.keys():
        raise ValueError(f"{var_name} could not be found in the VARS context")

    return context.vars[var_name]

def process_secret(context, var_name: str) -> str:
    if var_name not in context.secrets.keys():
        raise ValueError(f"{var_name} could not be found in the SECRETS context")

    return context.secrets[var_name]

def process_env(context, var_name: str) -> str:
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
            preprocessor: PreProcessor = PreProcessor(config_file.read())
            config_str: str = preprocessor.preprocess({
                "vars": lambda v: process_var(context, v),
                "secrets": lambda s: process_secrets(context, s),
                "env": lambda e: process_env(context, e),
            })
        else:
            config_str: str = config_file.read()

        config_data: dict = yaml.safe_load(config_str)

        validate(
            instance=config_data,
            schema=helper_get_config_schema(schema_path),
        )

        return config_data
