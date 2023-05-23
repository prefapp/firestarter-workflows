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
        task_manager_data = yaml.load(task_manager.read(), Loader=yaml.Loader)
        validate(
            instance=task_manager_data, schema=helper_get_task_manager_schema()
        )
        return task_manager_data
