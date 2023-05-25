from .config_parser import Parser
from jsonschema import validate
import os
import json
import yaml


def helper_get_task_manager_schema():
    TASK_MANAGER_SCHEMA = False

    with open(os.path.join(
        os.path.dirname(__file__), 'task_manager.schema.json'
    )) as schema:
        TASK_MANAGER_SCHEMA = json.load(schema)

    return TASK_MANAGER_SCHEMA


def validate_task_manager(task_manager_path):
    with open(task_manager_path, 'r') as task_manager:
        read_task_manager: str = task_manager.read()
        task_manager_data = yaml.load(read_task_manager, Loader=yaml.Loader)
        parser: Parser = Parser(read_task_manager)

        for symbol in parser.parse():
            context, var = symbol.split(".")

            if context == "env":
                parser.interpolate(symbol, os.environ[var])
            elif context == "vars":
                parser.interpolate(symbol, "")
            elif context == "secrets":
                parser.interpolate(symbol, "")
            else:
                raise ValueError(
                    "Variable context unknown (incorrect placeholder)"
                )

        task_manager_data = yaml.load(parser.data, Loader=yaml.Loader)
        validate(
            instance=task_manager_data, schema=helper_get_task_manager_schema()
        )
        return task_manager_data
