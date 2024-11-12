from abc import abstractmethod
import json
from os import getenv, path
from dataclasses import dataclass
import base64

@dataclass
class RegistryAuth:
    username: str
    token: str

class RegistryProvider():

    def __init__(self, registry: str, creds: str = None) -> None:
        self._creds = creds
        self._registry = registry

    @property
    def registry(self):
        return self._registry

    @property
    def creds(self):
        return self._creds

    @creds.setter
    def creds(self, value):
        self._creds = value

    @abstractmethod
    def get_registry_auth(self):
        pass

    def login_registry(self):
        return self._base_login_registry()

    def _base_login_registry(self):
        print("Base login")

        auth = self.get_registry_auth()
        auth_string = f"{auth.username}:{auth.token}"
        b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

        docker_cfg_path = f"{getenv('HOME')}/.docker/config.json"
        if not path.exists(docker_cfg_path):
            config = {}
        else:
            with open(docker_cfg_path, 'r') as f:
                config = json.load(f)

        config.setdefault("auths", {})[self.registry] = {"auth": b64_auth}

        # Write the updated config to config.json
        with open(docker_cfg_path, "w") as f:
            json.dump(config, f, indent=2)

        return True

    def _oauth_login_registry(self):
        print("Oauth login")
        auth = self.get_registry_auth()
        auth_string = f"{auth.username}:"
        b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
        docker_cfg_path = f"{getenv('HOME')}/.docker/config.json"
        if not path.exists(docker_cfg_path):
            config = {}
        else:
            with open(docker_cfg_path, 'r') as f:
                config = json.load(f)
        config.setdefault("auths", {})[self.registry] = {
            "auth": b64_auth,
            "identitytoken": auth.token
        }

        # Write the updated config to config.json
        with open(docker_cfg_path, "w") as f:
            json.dump(config, f, indent=2)

        return True
