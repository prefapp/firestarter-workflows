from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List
import boto3.session
import json
from os import getenv, path

class DockerRegistryAuthFactory():

    def provider_from_str(provider: str) -> Provider:
        if provider == 'aws_oidc':
            return AwsOidcDockerRegistryAuth()
        elif provider == 'azure_oidc':
            return AzureOidcDockerRegistryAuth()
        elif provider == 'generic':
            return GenericDockerRegistryAuth()
        else:
            raise ValueError(f'Unknown provider: {provider}')


class Provider():

    def login_registry(self, registry, auth):
        docker_cfg_path = f"{getenv('HOME')}/.docker/config.json"
        if not path.exists(docker_cfg_path):
            config = {}
        else:
            with open(docker_cfg_path, 'r') as f:
                config = json.load(f)
        config.setdefault("auths", {})[registry] = {"auth": auth}

        # Write the updated config to config.json
        with open(docker_cfg_path, "w") as f:
            json.dump(config, f, indent=2)


class AwsOidcDockerRegistryAuth(Provider):

    def get_registry_auth(self):
        session = boto3.session.Session()
        ecr = session.client('ecr')
        auth = ecr.get_authorization_token()
        authorization_token = auth['authorizationData'][0]['authorizationToken']
        return authorization_token

class AzureOidcDockerRegistryAuth(Provider):

    def get_registry_auth(self):
        raise NotImplementedError('Azure OIDC not implemented yet')

class GenericDockerRegistryAuth(Provider):

    def get_registry_auth(self):
        raise NotImplementedError('Generic OIDC not implemented yet')
