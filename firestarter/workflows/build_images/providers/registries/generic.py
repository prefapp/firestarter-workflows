from .base import RegistryAuth, RegistryProvider


class GenericDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        if self.creds is None:
            raise ValueError("Credentials not set")
        # split the username and password
        username, token = self.creds.split(":")
        return RegistryAuth(username=username, token=token)
