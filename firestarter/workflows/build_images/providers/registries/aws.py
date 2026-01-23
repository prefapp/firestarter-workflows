import boto3
from .base import RegistryProvider, RegistryAuth
import base64

class AwsOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        session = boto3.session.Session()
        ecr = session.client('ecr')
        auth = ecr.get_authorization_token()
        authorization_token = base64.b64decode(
            auth['authorizationData'][0]['authorizationToken'].encode()
        )

        username, token = authorization_token.decode().split(':')
        return RegistryAuth(username=username, token=token)
