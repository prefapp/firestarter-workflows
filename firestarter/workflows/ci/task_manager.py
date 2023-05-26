from firestarter.common.validations import validate_task_manager
from .tasks import TaskGroup, Task


def task_scheduler(task_manager_data: str, tasks_instance: TaskGroup) -> None:
    for index, task in enumerate(task_manager_data["tasks"]):
        task_obj: Task = Task(task, index)
        tasks_instance.add_task(task_obj)


class TaskManager:

    def __init__(self) -> None:
        self.tasks: TaskGroup = TaskGroup()
        self._context = False

    @property
    def context(self) -> dict:
        return self._context

    @context.setter
    def context(self, context) -> None:
        self._context = context

    def load(self, path: str, schema_path: str) -> None:
        task_manager_data: dict = validate_task_manager(path, schema_path)

        # init the context properly
        self.context.default_image = task_manager_data["image"]
        self.context.default_env = task_manager_data.get("vars", {})

        # let's load the tasks
        task_scheduler(task_manager_data, self.tasks)

    def run(self) -> None:
        self.tasks.run_tasks(self.context)

