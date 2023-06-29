from .aws import AwsOidcDockerRegistryAuth
from .azure import AzureOidcDockerRegistryAuth
from .generic import GenericDockerRegistryAuth
from .base import RegistryProvider


class DockerRegistryAuthFactory():

    def provider_from_str(provider: str, registry) -> RegistryProvider:
        if provider == 'aws_oidc':
            return AwsOidcDockerRegistryAuth(registry)
        elif provider == 'azure_oidc':
            return AzureOidcDockerRegistryAuth(registry)
        elif provider == 'generic':
            return GenericDockerRegistryAuth(registry)
        else:
            raise ValueError(f'Unknown provider: {provider}')
