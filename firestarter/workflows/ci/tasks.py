from .bash_runner import exec_run_in_container
if TYPE_CHECKING:
    from dagger import Container

class Task:

    def __init__(self, args: dict, order: int = 0):
        self.order: int = order
        self.name: str = args["name"]
        self.commands: List[str] = args["run"]
        self.image: str = args.get("image", None)
        self.env: dict = args.get("vars", {})

    def execute(self, ctx: dict) -> None:
        container: Container = self.prepare_ctx(ctx)
        container = exec_run_in_container(
            self.commands, container, ctx.dagger_client
        )

        if container.exit_code() != 0:
            raise f"ERROR: {self.name}: {container.stderr()} {container.stdout()}"

        ctx.set_output(self.name, container)

    def prepare_ctx(self, ctx: dict) -> Container:
        container: Container = ctx.next_container(self.image)
        return self.add_env(container, ctx)

    def add_env(self, container: Container, ctx: dict) -> Container:
        env = dict(ctx.default_env, **self.env)

        for env_name, env_value in env.items():
            container = container.with_env_variable(env_name, env_value)

        return container


class TaskGroup:

    def __init__(self) -> None:
        self.__tasks = {}

    def add_task(self, task: Task) -> None:
        if not isinstance(task, Task):
            raise f"Added task is not of type Task"

        if task.name in self.__tasks:
            raise f"There are already a task named {task.name}"

        self.__tasks[task.name] = task

    def run_tasks(self, context: dict) -> None:
        ctx = context

        for task in sorted(self.__tasks.values(), key=lambda t: t.order):
            task.execute(ctx)
