from abc import abstractmethod
from abc import ABC, abstractmethod
from typing import List
import boto3.session
import re

class SecretProvider():
    def __init__(self, secret: str) -> None:
        self._secret = secret

    @property
    def secret(self):
        return self._secret

    @abstractmethod
    def get_secret(self):
        raise NotImplementedError('get_secret not implemented')

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
