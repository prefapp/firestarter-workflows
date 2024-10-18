import datetime
import json
import re
import os
import sys
from firestarter.common.firestarter_workflow import FirestarterWorkflow
import anyio
import dagger
from .providers.registries.factory import DockerRegistryAuthFactory
from .providers.secrets.resolver import SecretResolver
from .config import Config
import docker
import uuid
from os import getenv, getcwd
import string
import logging
import fnmatch
import subprocess
from ruamel.yaml import YAML

logger = logging.getLogger(__name__)
yaml = YAML(typ='safe')


def normalize_image_tag(tag):
    valid_chars = string.ascii_letters + string.digits + '_.-'

    # replace invalid characters with '-'
    tag = ''.join(c if c in valid_chars else '-' for c in tag)

    return tag

class BuildImages(FirestarterWorkflow):
    SCHEMA_FILE_PATH: str = os.path.join(os.path.dirname(__file__), 'resources/schema.json')

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self._secrets = self.resolve_secrets(self.secrets)

        # We checkout the correct sha/tag
        self._from = self.dereference_from_input(self.vars.get('from'))
        self._repo_name = self.vars.get('repo_name')
        self._snapshots_registry = self.vars.get('snapshots_registry')
        self._releases_registry = self.vars.get('releases_registry')
        self._snapshots_registry_creds = self.vars.get('snapshots_registry_creds', None)
        self._releases_registry_creds = self.vars.get('releases_registry_creds', None)
        self._auth_strategy = self.vars.get('auth_strategy', None)
        self._output_results = self.vars.get('output_results', 'results.yaml')
        self._type = self.vars.get('type', 'snapshots')
        self._workflow_run_id = self.vars.get('workflow_run_id', None)
        self._workflow_run_url = self.vars.get('workflow_run_url', None)
        self._service_path = self.vars.get('service_path', '')
        self._flavors = self.vars.get('flavors', 'default')
        self._container_structure_filename = self.vars.get(
            'container_structure_filename', None
        )
        self._login_required = self.vars.get('login_required', True)
        self._publish = self.vars.get('publish', True)

        # Read the configuration file
        self._dagger_secrets = []
        self._config = Config.from_yaml(
            self.config_file,
            self.type,
            self.secrets,
            schema_file = self.SCHEMA_FILE_PATH
        )

    def _required_vars(self):
        return ['from', 'repo_name', 'snapshots_registry', 'releases_registry']

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
    def snapshots_registry_creds(self):
        return self._snapshots_registry_creds

    @property
    def releases_registry_creds(self):
        return self._releases_registry_creds

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
    def workflow_run_id(self):
        return self._workflow_run_id

    @property
    def workflow_run_url(self):
        return self._workflow_run_url

    @property
    def workflow_run_id(self):
        return self._workflow_run_id

    @property
    def workflow_run_url(self):
        return self._workflow_run_url

    @property
    def flavors(self):
        return self._flavors

    @property
    def service_path(self):
        return self._service_path

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
    def output_results(self):
        return self._output_results

    def execute(self):
        self.checkout_git_repository(self.from_version)

        if self.is_auto_build():
            self.filter_auto_build()
        else:
            self.filter_flavors()

        if self.login_required:
            self.login(
                self.auth_strategy,
                default_registry,
                default_registry_creds,
            )

        for flavor in self.flavors:
            logger.info(f"Building flavor {flavor}...")
            flavor_data = self.config.images[flavor]

            if flavor_data.registry:
                flavor_registry_data = self.get_flavor_registry_data(flavor_data)
                self.login(
                    flavor_registry_data.auth_strategy,
                    flavor_registry_data.name,
                    flavor_registry_data.creds
                )

            extra_registries = value.extra_registries or []

            for extra_registry in extra_registries:
                if extra_registry['auth_strategy']:
                    self.login(
                        extra_registry['auth_strategy'],
                        extra_registry['name'],
                        default_registry_creds
                    )

        logger.info(f"Building images for {self.flavors} flavors...")

        # Run the coroutine function to execute the compilation
        # process for all flavors
        return anyio.run(self.compile_images_for_all_flavors)

    def checkout_git_repository(self, checkout_value):
        proc = subprocess.run(["git", "checkout", checkout_value])
        proc.check_returncode()

    def dereference_from_input(self, input_value):
        # If the input value is a valid git sha or tag, return it
        if re.match(r'^[0-9a-f]{40}$', input_value, re.IGNORECASE) or\
                re.match(r'^[0-9a-f]{7}$', input_value, re.IGNORECASE):
            return input_value[:7]

        # git tag -l <pattern> checks to see if any tag matches the given pattern.
        # Since we want a tag named exactly as input_value, we input it as a pattern
        # and check the output. If it's empty, input_value is not a tag. If it does,
        # input_value is a tag
        proc = subprocess.run(
            ['git', 'tag', '-l', input_value], stdout=subprocess.PIPE
        )
        proc.check_returncode()
        git_output = proc.stdout.decode('utf-8').strip()

        if git_output:
            return git_output

        # if the input value is a branch, we need to get the sha of the branch
        proc = subprocess.run(
            ['git', 'rev-parse', f"origin/{input_value}"], stdout=subprocess.PIPE
        )
        proc.check_returncode()
        return proc.stdout.decode('utf-8')[:7]

    def resolve_secrets(self, secrets=None):
        sr = SecretResolver(secrets)
        return sr.resolve()

    def filter_flavors(self):
        all_flavors_list = list(self.config.to_dict()["images"].keys())
        flavor_filter_list = []
        final_flavors_list = []

        # Get the flavors to build from the command-line arguments and filter
        # the flavors configured accordingly
        if self.flavors.replace(' ', '') == '*':
            logger.info('Publishing all flavors:')
            self._flavors = ",".join(all_flavors_list)

        flavor_filter_list = self.flavors.replace(' ', '').split(',')
        for flavor in all_flavors_list:
            for flavor_filter in flavor_filter_list:
                if fnmatch.fnmatch(flavor, flavor_filter):
                    final_flavors_list.append(flavor)
                    continue

        self._flavors = final_flavors_list


    def filter_auto_build(self):
        logger.info(
            'Publishing all flavors with auto build enabled:',
            self.config.to_dict()["images"]
        )
        self._flavors = [
            flavor for flavor in self.config.to_dict()["images"]
            if self.config.to_dict()["images"][flavor].get("auto")
        ]

    async def test_image(self, ctx):
        try:
            file_name = f"{str(uuid.uuid4())}.tar"
            await ctx.export(file_name)
            client = docker.DockerClient(base_url='unix://var/run/docker.sock')

            with open(file_name, "rb") as f:
                data = f.read()
                image  = client.images.load(data)

            stdout = client.containers.run(
                'gcr.io/gcp-runtimes/container-structure-test',
                f'test -i {image[0].id} --config /tmp/cwd/{self.container_structure_filename}',
                detach=False,
                mounts=[{
                    'source': '/var/run/docker.sock',
                    'target': '/var/run/docker.sock',
                    'type': 'bind'
                }, {
                    'source': getcwd(),
                    'target': '/tmp/cwd',
                    'type': 'bind'
                }]
            )

            logger.info(stdout.decode('utf-8'))

        except docker.errors.ContainerError as e:
            raise Exception("Structure test failed.")
        except Exception as e:
            logger.info(e)
        finally:
            os.remove(file_name)


    # Define a coroutine function to compile an image using Docker
    async def compile_image_and_publish(
        self, ctx, build_args, secrets, dockerfile, image
    ):
        # Set a current working directory
        src = ctx.host().directory(".")

        logger.info(f"Using secrets: {secrets}")

        ctx = (
            ctx.container()
                .build(
                    context=src,
                    dockerfile=dockerfile,
                    build_args=build_args,
                    secrets=secrets
                )
                .with_label("source.code.revision", self.from_version)
                .with_label("repository.name", self.repo_name)
                .with_label("build.date", datetime.datetime.now().strftime(
                    "%Y-%m-%d_%H:%M:%S_UTC"
                ))
        )

        if self.container_structure_filename is not None:
            await self.test_image(ctx)

        if self.publish:
            await ctx.publish(address=f"{image}")

    # Define a coroutine function to execute the compilation process
    # for all flavors
    async def compile_images_for_all_flavors(self):
        # Set up the Dagger configuration object
        config = dagger.Config(log_output=sys.stdout)
        results_list = []

        # Connect to Dagger
        async with dagger.Connection(config) as client:

            secrets_for_all_flavors = []
            for key, value in self.secrets.items():
                secrets_for_all_flavors.append(client.set_secret(key, value))

            logger.info(
                f"Using these secrets for all flavors: {self.secrets.keys()}"
            )

            for flavor in self.flavors:
                registry, full_repo_name, build_args,\
                        dockerfile, extra_registries = self.get_flavor_data(flavor)

                # Set the build arguments for the current flavor
                build_args_list = [
                    dagger.BuildArg(name=key, value=value)
                    for key, value in build_args.items()
                ]

                resolved_secret_refs = self.resolve_secrets(
                    self.config.images[flavor].secrets or {}
                )

                logger.info((
                    f"Setting flavor {flavor} custom secrets: "
                    f"{resolved_secret_refs.keys()}"
                ))

                # Create an empty list to store the Dagger secrets for the
                # custom secrets for this flavor
                flavor_secrets = []

                for key, value in resolved_secret_refs.items():
                    flavor_secrets.append(client.set_secret(key, value))

                # Combine generic and custom secrets for this flavor
                secrets = secrets_for_all_flavors + flavor_secrets

                # Set the address for the default registry
                registry_address = f"{registry}/{full_repo_name}"

                logger.info(f"Registry address 🍄: {registry_address}")
                full_registry_address = (
                    f"{registry_address}:"
                    f"{normalize_image_tag(self.from_version + '_' + flavor)}"
                )

                # Create a list of addresses for all registries
                registry_list = [full_registry_address]

                for extra_registry in extra_registries:
                    extra_registry_address = (
                        f"{extra_registry['name']}/"
                        f"{extra_registry['repository']}"
                    )
                    extra_full_registry_address = (
                        f"{extra_registry_address}:"
                        f"{normalize_image_tag(self.from_version + '_' + flavor)}"
                    )
                    registry_list.append(extra_full_registry_address)

                for image in registry_list:
                    await self.compile_image_and_publish(
                        client,
                        build_args_list,
                        secrets,
                        dockerfile,
                        image
                    )

                    image_tag = image.split(":")[1]
                    registry = image.split(":")[0].split("/")[0]
                    repository = "/".join(image.split(":")[0].split("/")[1:])

                    results_list.append({
                        "flavor": flavor,
                        "image_type": self.type,
                        "version": self.from_version,
                        "image_repo": self.repo_name,
                        "image_tag": image_tag,
                        "repository": repository,
                        "registry": registry,
                        "build_args": build_args,
                        "workflow_run_id": self.workflow_run_id,
                        "workflow_run_url": self.workflow_run_url
                    })

        yaml.default_flow_style = False
        with open(os.path.join("/tmp", self.output_results), "w") as f:
            yaml.dump(results_list, f)

        return results_list

    def get_flavor_data(self, flavor):
        flavor_data = self.config.images[flavor]

        flavor_registry_data = self.get_flavor_registry_data(flavor_data)
        build_args = flavor_data.build_args or {}
        dockerfile = flavor_data.dockerfile or ""
        extra_registries = flavor_data.extra_registries or []

        return (
            flavor_registry_data["name"],
            flavor_registry_data["full_repo_name"],
            build_args,
            dockerfile,
            extra_registries
        )

    def get_flavor_registry_data(self, flavor_data):
        def concat_full_repo_name(service_path, repo_name):
            if not service_path:
                return repo_name
            else:
                return f"{service_path}/{repo_name}"

        flavor_registry = flavor_data.registry or {}
        flavor_registry_data = {
            "name": flavor_registry.get(
                "name", self.vars[f"{self.type}_registry"]
            ),
            "full_repo_name": flavor_registry.get(
                "repository", concat_full_repo_name(
                    self.service_path, self.repo_name
                )
            ),
            "auth_strategy":flavor_registry.get(
                "auth_strategy", self.auth_strategy
            ),
            "creds": flavor_registry.get(
                "creds", self.vars[f"{self.type}_registry_creds"]
            ),
        }

        return flavor_registry_data


    def is_auto_build(self):
        return self.flavors is None or self.flavors.replace(' ', '') == ''

    def login(self, auth_strategy, registry, creds):
        logger.info(f"Logging in to {registry} using {auth_strategy}...")

        # Log in to the default registry
        provider = DockerRegistryAuthFactory.provider_from_str(
            auth_strategy, registry
        )

        logger.info(f"Setting creds {creds}")
        provider.creds = creds

        provider.login_registry()

