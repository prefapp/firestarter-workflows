import docker

class DaggerContextMock():
    throw_docker_container_error = False
    throw_generic_error = False

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



class DaggerImageMock():
    id = "1234"

    def __init__(self, new_id):
        id = new_id
