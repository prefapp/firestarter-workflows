from firestarter.common.validations import validate_config
from .tasks import TaskGroup, Task


def task_scheduler(config_data: str, tasks_instance: TaskGroup) -> None:
    for index, task in enumerate(config_data["tasks"]):
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
        config_data: dict = validate_config(path, schema_path, self.context)

        # init the context properly
        self.context.default_image = config_data["image"]
        self.context.default_env = config_data.get("vars", {})

        # let's load the tasks
        task_scheduler(config_data, self.tasks)

    def run(self) -> None:
        self.tasks.run_tasks(self.context)

