from jsonschema import validate
import os
import json
import yaml


def helper_get_workflow_schema():
    WORKFLOW_SCHEMA = False

    with open(os.path.join(
        os.path.dirname(__file__), 'workflow.schema.json'
    )) as schema:
        WORKFLOW_SCHEMA = json.load(schema)

    return WORKFLOW_SCHEMA


def validate_workflow(workflow_path):
    with open(workflow_path, 'r') as workflow:
        workflow_data = yaml.load(workflow.read(), Loader=yaml.Loader)
        validate(instance=workflow_data, schema=helper_get_workflow_schema())
        return workflow_data
