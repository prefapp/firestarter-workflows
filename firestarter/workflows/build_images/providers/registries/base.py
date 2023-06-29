from abc import abstractmethod
import json
from os import getenv, path


class RegistryProvider():

    def __init__(self, registry: str) -> None:
        self._registry = registry

    @property
    def registry(self):
        return self._registry

    @abstractmethod
    def get_registry_auth(self):
        pass

    def login_registry(self):
        docker_cfg_path = f"{getenv('HOME')}/.docker/config.json"
        if not path.exists(docker_cfg_path):
            config = {}
        else:
            with open(docker_cfg_path, 'r') as f:
                config = json.load(f)
        config.setdefault("auths", {})[self.registry] = {"auth": self.get_registry_auth()}

        # Write the updated config to config.json
        with open(docker_cfg_path, "w") as f:
            json.dump(config, f, indent=2)
