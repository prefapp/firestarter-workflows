import sys
import anyio
import dagger
from typing import Callable

class Context:

    def __init__(self, vars: dict = None, secrets: dict = None) -> None:
        self.container: dagger.Container = False
        self._dagger_client: dagger.Client = False
        self._default_image: str = False
        self._default_env: dict = {}
        self.outputs: dict = {}
        self.vars: dict = vars if vars else {}
        self.secrets: dict = secrets if secrets else {}

    async def start(self, fn: Callable) -> None:
        with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            self.dagger_client = client
            fn(self)

    @property
    def dagger_client(self) -> dagger.Client:
        return self._dagger_client

    @property
    def default_image(self) -> str:
        return self._default_image

    @property
    def default_env(self) -> dict:
        return self._default_env

    @dagger_client.setter
    def dagger_client(self, dagger_client: dagger.Client) -> None:
        self._dagger_client = dagger_client

    @default_image.setter
    def default_image(self, image: str) -> None:
        self._default_image = image

    @default_env.setter
    def default_env(self, env: dict) -> None:
        self._default_env = env

    def next_container(self, image: str = None) -> dagger.Container:
        if not image:
            image = self.default_image
        else:
            self.container = False

        if self.container:
            return self.container
        else:
            return self.new_container(image)

    def new_container(self, image: str) -> dagger.Container:
        return self.dagger_client.container().from_(image)

    def set_output(self, name: str, container: dagger.Container) -> None:
        self.container = container
        self.outputs[name] = container.stdout()
