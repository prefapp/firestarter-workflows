from .dagger_context import Context
from .task_manager import TaskManager
import anyio
import os


SCHEMA_FILE_PATH: str = os.path.join(os.path.dirname(__file__), 'schema.json')


class CI:

    def __init__(self, file_path: str, context: Context):
        self.file_path = file_path
        self.context = context

    def execute(self):

        def init_task_manager(context):
            tm = TaskManager()
            tm.context = self.context
            tm.load(self.file_path, SCHEMA_FILE_PATH)
            tm.run()

        anyio.run(lambda: self.context.start(init_task_manager))
