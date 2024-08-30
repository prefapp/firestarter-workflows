import base64
import json
import os
from .base import RegistryAuth, RegistryProvider


class DockerHubRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        if self.creds is None:
            raise ValueError("Credentials not set")
        # split the username and password
        username, token = self.creds.split(":")
        return RegistryAuth(username=f"{username}", token=token)
    
    def _base_login_registry(self):
        print("DockerHub login")

        auth = self.get_registry_auth()
        auth_string = f"{auth.username}:{auth.token}"
        b64_auth = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

        docker_cfg_path = f"{os.getenv('HOME')}/.docker/config.json"
        if not os.path.exists(docker_cfg_path):
            config = {}
        else:
            with open(docker_cfg_path, 'r') as f:
                config = json.load(f)
        config.setdefault("auths", {})[f"https://{self.registry}/v1/"] = {"auth": b64_auth}

        # Write the updated config to config.json
        with open(docker_cfg_path, "w") as f:
            json.dump(config, f, indent=2)
