from dagger_helper import validations
from dagger_helper.tasks import Tasks, Task


def task_scheduler(task_manager_data, tasks_instance, context):
    for index, task in enumerate(task_manager_data["tasks"]):
        task_obj = Task(task, index)
        tasks_instance.add_task(task_obj)


class TaskManager:

    def __init__(self):
        self.tasks = Tasks()
        self._context = False

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, context):
        self._context = context

    def load(self, path):
        task_manager_data = validations.validate_task_manager(path)

        # init the context properly
        self.context.default_image = task_manager_data["image"]
        self.context.default_env = task_manager_data.get("env", {})

        # let's run the tasks
        task_scheduler(task_manager_data, self.tasks, self.context)

    def run(self):
        self.tasks.run_tasks(self.context)

