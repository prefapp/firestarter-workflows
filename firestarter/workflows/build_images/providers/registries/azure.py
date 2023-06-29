
from .base import RegistryProvider


class AzureOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        raise NotImplementedError('Azure OIDC not implemented yet')
