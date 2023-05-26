from .dagger_context import Context
from .task_manager import TaskManager
import anyio


class CI:

    def __init__(self, file_path: str, context: Context):
        self.file_path = file_path
        self.context = context

    def execute(self):

        def init_task_manager(context):
            tm = TaskManager()
            tm.context = self.context
            tm.load(self.file_path)
            tm.run()

        anyio.run(lambda: self.context.start(init_task_manager))
