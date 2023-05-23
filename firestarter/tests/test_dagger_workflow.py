from firestarter.common.dagger_context import Context
from firestarter.common.task_manager import TaskManager
import anyio
import os


def test_dagger_workflow():

    def myTestFunc(context):
        tm = TaskManager()
        tm.context = context
        tm.load(os.path.join(
            os.path.dirname(__file__), 'fixtures/test_workflow.yaml'
        ))
        tm.run()

    anyio.run(lambda: Context().start(myTestFunc))

