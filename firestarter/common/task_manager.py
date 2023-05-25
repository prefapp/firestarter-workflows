from .validations import validate_task_manager
from .tasks import TaskGroup, Task
from .config_parser import parse_vars


def task_scheduler(task_manager_data, tasks_instance, context):
    for index, task in enumerate(task_manager_data["tasks"]):
        task_obj = Task(task, index)
        tasks_instance.add_task(task_obj)


class TaskManager:

    def __init__(self):
        self.tasks = TaskGroup()
        self._context = False

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context):
        self._context = context

    def load(self, path: str) -> None:
        task_manager_data: dict = validate_task_manager(path)

        # init the context properly
        self.context.default_image: str = task_manager_data["image"]
        self.context.default_env: dict = parse_vars(
            task_manager_data.get("vars", {})
        )

        # let's run the tasks
        task_scheduler(task_manager_data, self.tasks, self.context)

    def run(self):
        self.tasks.run_tasks(self.context)

