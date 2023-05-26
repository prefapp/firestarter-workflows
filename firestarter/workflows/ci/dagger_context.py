import sys
import anyio
import dagger

class Context:

    def __init__(self):
        self.container = False
        self._dagger_client = False
        self._default_image = False
        self._default_env = {}
        self.outputs = {}

    async def start(self, fn):
        with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
            self.dagger_client = client
            fn(self)

    @property
    def dagger_client(self):
        return self._dagger_client

    @property
    def default_image(self):
        return self._default_image

    @property
    def default_env(self):
        return self._default_env

    @dagger_client.setter
    def dagger_client(self, dagger_client):
        self._dagger_client = dagger_client

    @default_image.setter
    def default_image(self, image):
        self._default_image = image

    @default_env.setter
    def default_env(self, env):
        self._default_env = env

    def next_container(self, image=None):
        if not image:
            image = self.default_image
        else:
            self.container = False

        if self.container:
            return self.container
        else:
            return self.new_container(image)

    def new_container(self, image):
        return self.dagger_client.container().from_(image)

    def set_output(self, name, container):
        self.container = container
        self.outputs[name] = container.stdout()
