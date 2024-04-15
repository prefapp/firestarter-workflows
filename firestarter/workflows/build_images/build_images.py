import datetime
import os
import sys
from firestarter.common.firestarter_workflow import FirestarterWorkflow
import anyio
import dagger
from .providers.registries.factory import DockerRegistryAuthFactory
from .providers.secrets.resolver import SecretResolver
from .config import Config
import docker
from ast import literal_eval
import uuid
from os import remove, getcwd
import string
import logging

logger = logging.getLogger(__name__)


def normalize_image_tag(tag):
    valid_chars = string.ascii_letters + string.digits + '.-'

    # replace invalid characters with '-'
    tag = ''.join(c if c in valid_chars else '-' for c in tag)

    return tag

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
        self._config = Config.from_yaml(
            self.config_file, self.type, self.secrets)

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

    def resolve_secrets(self, secrets=None):
        sr = SecretResolver(secrets)
        return sr.resolve()

    def filter_flavors(self):
        # Get the on-premises name from the command-line arguments and filter the on-premises data accordingly
        if self.flavors is not None:
            if self.flavors.replace(' ', '') == '*':
                print('Publishing all flavors:')
                self._flavors = ",".join(list(self.config.to_dict()["images"].keys()))

            self._flavors = self.flavors.replace(' ', '').split(',')


    async def test_image(self, ctx):
        try:
            file_name = f"{str(uuid.uuid4())}.tar"
            await ctx.export(file_name)
            client = docker.DockerClient(base_url='unix://var/run/docker.sock')

            with open(file_name, "rb") as f:
                data = f.read()
                image  = client.images.load(data)

            stdout = client.containers.run(
                'gcr.io/gcp-runtimes/container-structure-test', f'test -i {image[0].id} --config /tmp/cwd/{self.container_structure_filename}',
                detach=False,
                mounts=[{
                    'source': '/var/run/docker.sock', 'target': '/var/run/docker.sock', 'type': 'bind'
                    }, {
                    'source': getcwd(), 'target': '/tmp/cwd', 'type': 'bind'
                    }]
                )

            print(stdout.decode('utf-8'))

        except docker.errors.ContainerError as e:
            raise Exception("Structure test failed.")
        except Exception as e:
            print(e)
        finally:
            remove(file_name)


    # Define a coroutine function to compile an image using Docker

    async def compile_image_and_publish(self, ctx, build_args, custom_secrets, dockerfile, image):
        # Set a current working directory
        src = ctx.host().directory(".")

        secrets = self.dagger_secrets + custom_secrets

        ctx = (
            ctx.container()
            .build(context=src, dockerfile=dockerfile, build_args=build_args, secrets=secrets)
                .with_label("source.code.revision", self.from_version)
                .with_label("repository.name", self.repo_name)
                .with_label("build.date", datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S_UTC"))
        )

        if self.container_structure_filename is not None:
            await self.test_image(ctx)

        if self.publish:
            await ctx.publish(address=f"{image}")

    # Define a coroutine function to execute the compilation process for all on-premises
    async def compile_images_for_all_flavors(self):
        # Set up the Dagger configuration object
        config = dagger.Config(log_output=sys.stdout)

        # Connect to Dagger
        async with dagger.Connection(config) as client:
            client.container()

            for key, value in self.secrets.items():
                self._dagger_secrets.append(client.set_secret(key, value))

            # Set up a task group to execute the compilation process for all flavors in parallel
            async with anyio.create_task_group() as tg:
                for flavor in self.flavors:
                    value = self.config.images[flavor]
                    # Get the registry, repository, build arguments, Dockerfile path, and address for the current on-premises
                    registry = self.vars[f"{self.type}_registry"]
                    build_args = value.build_args or {}
                    dockerfile = value.dockerfile or ""
                    extra_registries = value.extra_registries or []

                    # Set the build arguments for the current on-premises
                    build_args_list = [dagger.BuildArg(name=key, value=value) for key, value in build_args.items()]

                    # Print the current on-premises data
                    print(f'\nOn-premise: {flavor.upper()}')
                    print(f'\tRegistry: {registry}')
                    print(f'\tRepository: {self.repo_name}')
                    if build_args != {}:
                        print(f'\tBuild args: {build_args}')
                    print(f'\tDockerfile: {dockerfile}')

                    custom_secrets = self.config.images[flavor].secrets or {}
                    custom_secrets = self.resolve_secrets(custom_secrets)

                    custom_dagger_secrets = []

                    for key, value in self.secrets.items():
                        custom_dagger_secrets.append(
                            client.set_secret(key, value))

                    # Set the address for the default registry
                    default_address = f"{registry}/{self.repo_name}"
                    default_image = f"{default_address}:{normalize_image_tag(self.from_version + '_' + flavor)}"
                    print(f'\tDefault image name: {default_image}')

                    registry_list = [default_image]

                    for extra_registry in extra_registries:
                        new_address = f"{extra_registry['name']}/{extra_registry['repository']}"
                        new_image = f"{new_address}:{normalize_image_tag(self.from_version + '_' + flavor)}"

                        registry_list.append(new_image)


                    for image in registry_list:
                        await tg.spawn(
                            self.compile_image_and_publish, client,
                            build_args_list, custom_dagger_secrets,
                            dockerfile, image
                        )


    def execute(self):
        self.filter_flavors()

        self.login(self.auth_strategy, getattr(self, f"{self.type}_registry"))

        for flavor in self.flavors:
            value = self.config.images[flavor]
            extra_registries = value.extra_registries or []

        for extra_registry in extra_registries:
            if extra_registry['auth_strategy']:
                self.login(
                    extra_registry['auth_strategy'],
                    extra_registry['name']
                )

        # Run the coroutine function to execute the compilation process for all on-premises
        anyio.run(self.compile_images_for_all_flavors)

    def login(self, auth_strategy, registry):

        # Log environment variables
        logger.info(f"Environment variables: {os.environ}")

        logger.info(f"Logging in to {registry} using {auth_strategy}...")

        if self.login_required and auth_strategy not in self.already_logged_in_providers:

            # Log in to the default registry
            provider = DockerRegistryAuthFactory.provider_from_str(
                auth_strategy, registry
            )

            provider.login_registry()

            self.already_logged_in_providers.append(auth_strategy)
        else:
            logger.info(
                f"Skipping login to {registry} as is already logged in.")
