from firestarter.common import validations
from firestarter.workflows.ci import task_manager
import os


class MockContext:
    pass

def test_validate_schema():
    validations.validate_task_manager(
        os.path.join(os.path.dirname(__file__), 'fixtures/workflow.yaml'),
        '../workflows/ci/schema.json',
    )

def test_validate_from_workflow():
    tm = task_manager.TaskManager()
    tm.context = MockContext()
    tm.load(
        os.path.join(os.path.dirname(__file__), 'fixtures/workflow.yaml'),
        '../workflows/ci/schema.json',
    )

