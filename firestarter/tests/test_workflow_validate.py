from firestarter.common.validations import validations
from firestarter.common.task_manager import TaskManager
import os


class MockContext:
    pass

def test_validate_schema():
    validations.validate_task_manager(
        os.path.join(os.path.dirname(__file__), 'fixtures/workflow.yaml')
    )

def test_validate_from_workflow():
    tm = TaskManager()
    tm.context = MockContext()
    tm.load(os.path.join(os.path.dirname(__file__), 'fixtures/workflow.yaml'))

