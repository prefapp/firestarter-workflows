from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from .base import SecretProvider

class AzureKeyVault():
    def __init__(self, secret) -> None:
        self._vault_name = secret.split('https://')[1].split('.vault.azure.net')[0]
        self._secret_name = secret.split('.vault.azure.net/secrets/')[-1].split('/')[0]

    @property
    def vault_name(self):
        return self._vault_name
    
    @property
    def secret_name(self):
        return self._secret_name

class AzureKeyVaultManager(SecretProvider):

    def __init__(self, secret: str) -> None:
        print("Initializing AwsSecretsManager")
        super().__init__(secret)
        self._credential = DefaultAzureCredential()

    @property
    def credential(self):
        return self._credential

    def get_secret(self):
        key_vault = AzureKeyVault(self.secret)
        client = SecretClient(vault_url=f"https://{key_vault.vault_name}.vault.azure.net", credential=self.credential)
        return client.get_secret(key_vault.secret_name).value
