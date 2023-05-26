from jsonschema import validate
import os
import json
import yaml


def helper_get_task_manager_schema(schema_path: str) -> dict:
    TASK_MANAGER_SCHEMA = False

    with open(os.path.join(os.path.dirname(__file__), schema_path)) as schema:
        TASK_MANAGER_SCHEMA = json.load(schema)

    return TASK_MANAGER_SCHEMA


def validate_task_manager(task_manager_path: str, schema_path: str) -> dict:
    with open(task_manager_path, 'r') as task_manager:
        task_manager_data: dict = yaml.load(
            task_manager.read(), Loader=yaml.Loader
        )

        validate(
            instance=task_manager_data,
            schema=helper_get_task_manager_schema(schema_path),
        )

        return task_manager_data
