from abc import abstractmethod

class SecretProvider():
    def __init__(self, secret: str) -> None:
        self._secret = secret

    @property
    def secret(self):
        return self._secret

    @abstractmethod
    def get_secret(self):
        raise NotImplementedError('get_secret not implemented')
