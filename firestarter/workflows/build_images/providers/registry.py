from abc import abstractmethod
import json
from os import getenv, path
import boto3.session

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

class AwsOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        session = boto3.session.Session()
        ecr = session.client('ecr')
        auth = ecr.get_authorization_token()
        authorization_token = auth['authorizationData'][0]['authorizationToken']
        return authorization_token

class AzureOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        raise NotImplementedError('Azure OIDC not implemented yet')

class GenericDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        raise NotImplementedError('Generic OIDC not implemented yet')
