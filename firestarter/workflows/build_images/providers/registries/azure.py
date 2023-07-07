
from .base import RegistryProvider, RegistryAuth
from azure.identity import DefaultAzureCredential
import requests
import base64

class AzureOidcDockerRegistryAuth(RegistryProvider):

    def get_registry_auth(self):
        credential = DefaultAzureCredential()
        aad_access_token = credential.get_token("https://management.azure.com/.default").token

        # Get the AAD refresh token
        
        data = {
            "grant_type": "access_token",
            "service": self.registry,
            "tenant": "common",
            "access_token": aad_access_token
        }
        acr_refresh_token = requests.post(
            f"https://{self.registry}/oauth2/exchange",
            data=data
        ).json()['refresh_token']

        # We should be able to use the access token. However, it doesn't work. So we use the refresh token instead.

        # Get the ACR access token
        # data = {
        #     "grant_type": "refresh_token",
        #     "service": self.registry,
        #     "scope": "registry:catalog:*",
        #     "refresh_token": acr_refresh_token
        # }

        # acr_access_token = requests.post(
        #     f"https://{self.registry}/oauth2/token",
        #     data=data
        # ).json()['access_token']


        # Generate the base64-encoded auth string
        auth = RegistryAuth(username="00000000-0000-0000-0000-000000000000", token=acr_refresh_token)
        return auth


    def login_registry(self):
        self._oauth_login_registry()
