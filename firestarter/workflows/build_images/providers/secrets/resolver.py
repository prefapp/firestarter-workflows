from typing import List

from .factory import SecretProviderFactory

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
