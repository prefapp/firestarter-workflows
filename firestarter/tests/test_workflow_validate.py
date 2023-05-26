from firestarter.common.validations import validate_task_manager
from firestarter.workflows.ci.task_manager import TaskManager
import os

CONFIG_FILE_PATH: str =\
    os.path.join(os.path.dirname(__file__), 'fixtures/workflow.yaml')

SCHEMA_FILE_PATH: str = '../workflows/ci/schema.json'


class MockContext:
    pass

def test_validate_schema() -> None:
    validate_task_manager(CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

def test_validate_from_workflow() -> None:
    tm: TaskManager = TaskManager()
    tm.context = MockContext()
    tm.load(CONFIG_FILE_PATH, SCHEMA_FILE_PATH)

