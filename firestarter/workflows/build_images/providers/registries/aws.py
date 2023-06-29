import boto3
from .base import RegistryProvider

class AwsOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        session = boto3.session.Session()
        ecr = session.client('ecr')
        auth = ecr.get_authorization_token()
        authorization_token = auth['authorizationData'][0]['authorizationToken']
        return authorization_token
