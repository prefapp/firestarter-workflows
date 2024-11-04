import docker
from typing_extensions import Self

class DaggerHostMock():
    def directory(self, path: str) -> bool:
        return DaggerDirectoryMock(path)


class DaggerDirectoryMock():
    path = ""

    def __init__(self, path: str):
        self.path = path


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
        return DaggerHostMock()

    async def publish(self, **kwargs) -> str:
        return "Mock publish result"

    def container(self) -> Self:
        return self

    def build(self, **kwargs) -> Self:
        self.context = kwargs["context"]
        self.dockerfile = kwargs["dockerfile"]
        self.build_args = kwargs["build_args"]
        self.secrets = kwargs["secrets"]

        return self

    def with_label(self, label_name: str, label_value) -> Self:
        self.label_list[label_name] = label_value

        return self


class DaggerImageMock():
    id = "1234"

    def __init__(self, new_id):
        id = new_id
