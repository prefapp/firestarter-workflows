import logging
import os
from .providers.secrets.resolver import SecretResolver
from firestarter.common.firestarter_workflow import FirestarterWorkflow
from ast import literal_eval
from .config import Config

from .providers.registries.factory import DockerRegistryAuthFactory
from .providers.secrets.resolver import SecretResolver

logger = logging.getLogger(__name__)

class BuildImages(FirestarterWorkflow):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._secrets = self.resolve_secrets(self.secrets)
        self._repo_name = self.vars['repo_name']
        self._snapshots_registry = self.vars['snapshots_registry']
        self._releases_registry = self.vars['releases_registry']
        self._auth_strategy = self.vars['auth_strategy']
        self._type = self.vars['type']
        self._from = self.vars['from']
        self._flavors = self.vars['flavors'] if 'flavors' in self.vars else 'default'
        self._container_structure_filename = self.vars['container_structure_filename'] if 'container_structure_filename' in self.vars else None
        self._dagger_secrets = []
        self._login_required = literal_eval(
            self.vars['login_required'].capitalize()) if 'login_required' in self.vars else True
        self._publish = self.vars['publish'] if 'publish' in self.vars else True
        self._already_logged_in_providers = []

        # Read the on-premises configuration file
        self._config = Config.from_yaml(self.config_file, self.type)
    def resolve_secrets(self, secrets=None):
        sr = SecretResolver(secrets)
        return sr.resolve()

    def filter_flavors(self):
        # Get the on-premises name from the command-line arguments and filter the on-premises data accordingly
        if self.flavors is not None:
            if self.flavors == '*':
                print('Publishing all flavors:')
                self._flavors = ",".join(list(self.config[self.type].keys()))

            self._flavors = self.flavors.replace(' ', '').split(',')

    def execute(self):
        self.filter_flavors()
        print(self._flavors)
        self.login(self.auth_strategy, getattr(self, f"{self.type}_registry"))

    def login(self, auth_strategy, registry):

        # Log environment variables
        logger.info(f"Logging in to {registry} using {auth_strategy}...")

        if self.login_required and auth_strategy not in self.already_logged_in_providers:

            # Log in to the default registry
            provider = DockerRegistryAuthFactory.provider_from_str(
                auth_strategy, registry
            )

            provider.login_registry()

            print(provider)

            self.already_logged_in_providers.append(auth_strategy)
        else:
            logger.info(
                f"Skipping login to {registry} as is already logged in.")


    @property
    def repo_name(self):
        return self._repo_name

    @property
    def snapshots_registry(self):
        return self._snapshots_registry

    @property
    def releases_registry(self):
        return self._releases_registry

    @property
    def auth_strategy(self):
        return self._auth_strategy

    @property
    def type(self):
        return self._type

    # Cannot use from property as it is a reserved keyword
    @property
    def from_version(self):
        return self._from

    @property
    def flavors(self):
        return self._flavors

    @property
    def container_structure_filename(self):
        return self._container_structure_filename

    @property
    def config(self):
        return self._config

    @property
    def dagger_secrets(self):
        return self._dagger_secrets

    @property
    def login_required(self):
        return self._login_required

    @property
    def publish(self):
        return self._publish

    @property
    def already_logged_in_providers(self):
        return self._already_logged_in_providers
