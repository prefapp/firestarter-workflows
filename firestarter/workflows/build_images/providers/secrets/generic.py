from .base import SecretProvider


class GenericSecretManager(SecretProvider):
    def get_secret(self):
        return self.secret
