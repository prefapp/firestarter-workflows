from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import boto3.session
import json
from os import getenv, path
import re

# Registry providers

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

# Secret providers

class SecretProviderFactory():
    
    def provider_from_str(secret: str) -> SecretProvider:
        
        arn_regex = r"^arn:aws:ssm:\w+(?:-\w+)+:\d{12}:parameter\/[a-zA-Z0-9\/-]+$"
        keyvault_regex = r"^WIP$"

        if re.match(arn_regex, secret):
            return AwsSecretsManager(secret)
        elif re.match(keyvault_regex, secret):
            return AzureKeyVaultManager(secret)
        else:
            return GenericSecretManager(secret)

class SecretProvider():
    def __init__(self, secret: str) -> None:
        self._secret = secret

    @property
    def secret(self):
        return self._secret

    @abstractmethod
    def get_secret(self):
        raise NotImplementedError('get_secret not implemented')

class AwsSecretsManager(SecretProvider):

    def __init__(self, secret: str) -> None:
        print("Initializing AwsSecretsManager")
        super().__init__(secret)
        session = boto3.session.Session()
        self._ssm = session.client('ssm')

    @property
    def ssm(self):
        return self._ssm

    def get_secret(self):
        ssm_name = self.secret.split(':parameter')[-1]
        return self.ssm.get_parameter(Name=ssm_name, WithDecryption=True)['Parameter']['Value']

class AzureKeyVaultManager(SecretProvider):
    pass

class GenericSecretManager(SecretProvider):
    def get_secret(self):
        return self.secret

class SecretResolver():

    def __init__(self, secrets: List[str]) -> None:
        self._secrets = secrets

    @property
    def secrets(self):
        return self._secrets

    def resolve(self):
        for key, value in self.secrets.items():
            secret_manager = SecretProviderFactory.provider_from_str(value)
            self.secrets[key] = secret_manager.get_secret()
        return self.secrets
