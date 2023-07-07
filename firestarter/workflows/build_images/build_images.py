import datetime
import sys
from firestarter.common.firestarter_workflow import FirestarterWorkflow
import anyio
import dagger
from .providers.registries.factory import DockerRegistryAuthFactory
from .providers.secrets.resolver import SecretResolver
from .config import Config
from azure.cli.core import get_default_cli
import docker
import uuid
from os import remove, getcwd

class BuildImages(FirestarterWorkflow):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._secrets = self.resolve_secrets()
        self._repo_name = self.vars['repo_name']
        self._from_point = self.vars['from_point']
        self._on_premises = self.vars['on_premises']
        self._container_structure_filename = self.vars['container_structure_filename'] if 'container_structure_filename' in self.vars else None
        self._dagger_secrets = []
        self._login_required = self.vars['login_required'] if 'login_required' in self.vars else True
        self._publish = self.vars['publish'] if 'publish' in self.vars else True

        # Read the on-premises configuration file
        self._config = Config.from_yaml(self.config_file)

    @property
    def repo_name(self):
        return self._repo_name

    @property
    def from_point(self):
        return self._from_point

    @property
    def on_premises(self):
        return self._on_premises

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

    def resolve_secrets(self):
        sr = SecretResolver(self.secrets)
        print(sr.resolve())
        return sr.resolve()

    def filter_on_premises(self):
        # Get the on-premises name from the command-line arguments and filter the on-premises data accordingly
        if self.on_premises is not None:
            if self.on_premises == '*':
                print('Publishing to all on-premises:')
                self._on_premises = ",".join(list(self.config.images.keys()))

            self._on_premises = self.on_premises.replace(' ', '').split(',')


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
    async def compile_image_and_publish(self, ctx, build_args, dockerfile, image):
        # Set a current working directory
        src = ctx.host().directory(".")
        
        ctx = (
            ctx.container()
                .build(context=src, dockerfile=dockerfile, build_args=build_args, secrets=self.dagger_secrets)
                .with_label("source.code.revision", self.from_point)
                .with_label("repository.name", self.repo_name)
                .with_label("build.date", datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S_UTC"))
        )

        if self.container_structure_filename is not None:
            await self.test_image(ctx)
        
        if self.publish:
            await ctx.publish(address=f"{image}")

    # Define a coroutine function to execute the compilation process for all on-premises
    async def compile_images_for_all_on_premises(self):
        # Set up the Dagger configuration object
        config = dagger.Config(log_output=sys.stdout)

        # Connect to Dagger
        async with dagger.Connection(config) as client:
            client.container()

            for key, value in self.secrets.items():
                self._dagger_secrets.append(client.set_secret(key, value))

            # Set up a task group to execute the compilation process for all on-premises in parallel
            async with anyio.create_task_group() as tg:
                for on_prem in self.on_premises:
                    value = self.config.images[on_prem]
                    # Get the registry, repository, build arguments, Dockerfile path, and address for the current on-premises
                    registry = value.registry
                    repository = value.repository
                    build_args = value.build_args or {}
                    dockerfile = value.dockerfile or ""

                    # Set the build arguments for the current on-premises
                    build_args_list = [dagger.BuildArg(name=key, value=value) for key, value in build_args.items()]

                    # Set the address for the current on-premises
                    address = f"{registry}/{repository}"
                    image = f"{address}:{self.from_point}"

                    # Print the current on-premises data
                    print(f'\nOn-premise: {on_prem.upper()}')
                    print(f'\tRegistry: {registry}')
                    print(f'\tRepository: {repository}')
                    if build_args != {}:
                        print(f'\tBuild args: {build_args}')
                    print(f'\tDockerfile: {dockerfile}')
                    print(f'\tImage name: {address}:{self.from_point}')

                    await tg.spawn(self.compile_image_and_publish, client, build_args_list, dockerfile, image)


    def execute(self):
        self.filter_on_premises()

        print(f"Building '{self.repo_name}' from '{self.from_point}' for '{self.on_premises}'")
        
        # Log in to the Azure Container Registry for each on-premises active in the configuration file
        for key in self.on_premises:
            on_prem = self.config.images[key]
            provider = DockerRegistryAuthFactory.provider_from_str(on_prem.auth_strategy, on_prem.registry)
            provider.login_registry()

        # Run the coroutine function to execute the compilation process for all on-premises
        # anyio.run(self.compile_images_for_all_on_premises)
