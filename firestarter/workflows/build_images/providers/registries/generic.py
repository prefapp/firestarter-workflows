from .base import RegistryProvider


class GenericDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        raise NotImplementedError('Generic OIDC not implemented yet')
