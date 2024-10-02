from .bash_runner import exec_run_in_container

class Task:

    def __init__(self, args: dict, order: int = 0):
        self.order: int = order
        self.name: str = args["name"]
        self.commands: List[str] = args["run"]
        self.image: str = args.get("image", None)
        self.env: dict = args.get("vars", {})

    async def execute(self, ctx) -> None:
        try:
            container = self.prepare_ctx(ctx)
            container = await exec_run_in_container(
                self.commands, container, ctx.dagger_client
            )

        except Exception:
            raise f"ERROR: {self.name}: {await container.stderr()} {await container.stdout()}"

        await ctx.set_output(self.name, container)

    def prepare_ctx(self, ctx):
        container = ctx.next_container(self.image)
        return self.add_env(container, ctx)

    def add_env(self, container, ctx):
        env: dict = dict(ctx.default_env, **self.env)

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

    async def run_tasks(self, context) -> None:
        ctx = context

        for task in sorted(self.__tasks.values(), key=lambda t: t.order):
            await task.execute(ctx)
