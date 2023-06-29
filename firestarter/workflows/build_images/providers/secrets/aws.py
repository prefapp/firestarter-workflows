from .base import SecretProvider
import boto3

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
