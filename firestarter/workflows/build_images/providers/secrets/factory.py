import re
from .aws import AwsSecretsManager
from .azure import AzureKeyVaultManager
from .base import SecretProvider
from .generic import GenericSecretManager


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
