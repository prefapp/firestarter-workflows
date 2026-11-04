from jsonschema import validate
from .preprocessor import PreProcessor
from collections import Counter
import os
import json
from ruamel.yaml import YAML


def process_context_var(context: dict, var_name: str, context_name: str) -> str:
    if var_name not in context.keys():
        raise ValueError(
            f"{var_name} could not be found in the {context_name} context"
        )

    return context[var_name]

def process_env_var(var_name: str, allow_undefined: bool = False) -> str:
    if var_name in os.environ:
        return os.environ[var_name]
    if allow_undefined:
        print(f"::warning::Environment variable '{var_name}' is undefined; "
              "replacing with an empty string")
        return ''
    raise ValueError(f"Environment variable '{var_name}' is undefined")

def helper_get_config_schema(schema_path: str) -> dict:
    CONFIG_SCHEMA = False

    with open(os.path.join(os.path.dirname(__file__), schema_path)) as schema:
        CONFIG_SCHEMA = json.load(schema)

    return CONFIG_SCHEMA


def validate_config(config_path: str, schema_path: str, context = None) -> dict:
    yaml=YAML(typ='safe')
    with open(config_path, 'r') as config_file:
        config_data: dict = yaml.load(config_file)
        if context is not None:
            try:
                config_data = PreProcessor(config_data).preprocess(context)
            except ValueError as error:
                raise ValueError(f"{error} in config '{config_path}'") from error

        validate(
            instance=config_data,
            schema=helper_get_config_schema(schema_path),
        )

        return config_data

def validate_config_extra_tags(config_data: dict) -> None:
    all_tags = []

    for image_type in config_data.values():
        for flavor in image_type.values():
            if "extra_tags" in flavor:
                all_tags.extend(flavor["extra_tags"])

    counts = Counter(all_tags)
    duplicates = [value for value, count in counts.items() if count > 1]

    if duplicates:
        raise ValueError(f"Duplicate extra_tags found: {', '.join(duplicates)}")
