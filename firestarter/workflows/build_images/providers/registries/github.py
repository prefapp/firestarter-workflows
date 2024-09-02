import os
from .base import RegistryAuth, RegistryProvider


class GithubRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        # split the username and password
        return RegistryAuth(username=os.environ['GITHUB_ACTOR'], token=os.environ['GH_TOKEN'])
