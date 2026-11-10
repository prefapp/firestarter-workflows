import docker
from typing_extensions import Self

class DaggerHostMock():
    def __init__(self, container):
        self.container = container

    def directory(self, path: str) -> bool:
        return DaggerDirectoryMock(path, self.container)


class DaggerDirectoryMock():
    path = ""

    def __init__(self, path: str, container):
        self.path = path
        self.container = container

    def docker_build(self, **kwargs):
        self.container.context = self
        self.container.platform = kwargs['platform']
        self.container.dockerfile = kwargs['dockerfile']
        self.container.build_args = kwargs['build_args']
        self.container.secrets = kwargs['secrets']
        return self.container

class DaggerContextMock():
    throw_docker_container_error = False
    throw_generic_error = False
    label_list = {}
    context = None
    dockerfile = ""
    build_args = None
    secrets = None

    def __init__(
        self,
        throw_docker_container_error=False,
        throw_generic_error=False
    ):
        self.throw_docker_container_error = throw_docker_container_error
        self.throw_generic_error = throw_generic_error

    async def export(self, file_name: str) -> None:
        if self.throw_docker_container_error:
            raise docker.errors.ContainerError(
                "Mock error docker", 1, "test", "test", "test"
            )

        if self.throw_generic_error:
            raise Exception("Mock error generic")

        print(f"Called mock with file_name ${file_name}")

    def host(self) -> DaggerHostMock:
        return DaggerHostMock(self)

    async def publish(self, **kwargs) -> str:
        return "Mock publish result"

    def container(self, platform = None) -> Self:
        return self

    def with_label(self, label_name: str, label_value) -> Self:
        self.label_list[label_name] = label_value

        return self


class DaggerImageMock():
    id = "1234"

    def __init__(self, new_id):
        id = new_id
