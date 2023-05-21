import sys
import dagger
import yaml
import datetime
from anyio import (
    run,
    create_task_group
)
from azure.cli.core import get_default_cli

def run(*, vars, secrets, config_file):
    # Define the path to the on-premises configuration file
    on_premises_config_path = './firestarter/workflows/on_premises/config.yaml'

    # Get the repository name from the command-line arguments
    repo_name = vars.get('repository_name', 'No repository name specified')

    # Get the code mapping label from the command-line arguments
    code_mapping_label = vars.get('code_mapping_label', 'No code mapping label specified'


# Read the on-premises configuration file
with open(on_premises_config_path, 'r') as f:
    on_premises_config_data = yaml.safe_load(f)

    # Get the on-premises name from the command-line arguments and filter the on-premises data accordingly
    on_premises = "*"
    if on_premises is not None:
        if on_premises == '*':
            print('Publishing to all on-premises:')
            on_premises = list(on_premises_config_data.keys())
            on_premises = ", ".join(on_premises)

        else:
            print(f'Publishing to on-premises:')

        on_premises = on_premises.replace(' ', '').split(',')
        on_premises_config_data = {key: value for key, value in on_premises_config_data.items() if key in on_premises}

        # Check if the on-premises exist
        for on_premise in on_premises:
            if on_premise not in on_premises_config_data.keys():
                print(f'\t- {on_premise} does not exist')
                print('Exiting...')
                sys.exit(1)


    # Print the filtered on-premises data
    for key, value in on_premises_config_data.items():
        print(f'\t- {key}')


# Define a coroutine function to execute the compilation process for all on-premises
async def compile_images_for_all_on_premises():
    # Set up the Dagger configuration object
    config = dagger.Config(log_output=sys.stdout)

    # Connect to Dagger
    async with dagger.Connection(config) as client:
        container = (
                client
                    .container()
            )

        # Set up a task group to execute the compilation process for all on-premises in parallel
        async with create_task_group() as tg:
            for key, value in on_premises_config_data.items():
                # Get the registry, repository, build arguments, Dockerfile path, and address for the current on-premises
                registry = value.get('registry', 'No registry specified')
                repository = value.get('repository', 'No repository specified')
                build_args = value.get('build_args', {})
                dockerfile = value.get('dockerfile', './docker/Dockerfile')

                # Set the build arguments for the current on-premises
                build_args_list = [dagger.BuildArg(name=key, value=value) for key, value in build_args.items()]

                # Set the address for the current on-premises
                address = f"{registry}/{repository}"
                image = f"{address}:{code_mapping_label}"

                # Print the current on-premises data
                print(f'\nOn-premise: {key.upper()}')
                print(f'\tRegistry: {registry}')
                print(f'\tRepository: {repository}')
                if build_args != {}:
                    print(f'\tBuild args: {build_args}')
                print(f'\tDockerfile: {dockerfile}')
                print(f'\tImage name: {address}:{code_mapping_label}')

                await tg.spawn(compile_image_and_publish, client, registry, build_args_list, dockerfile, image)


# Define a coroutine function to compile an image using Docker
async def compile_image_and_publish(ctx, registry, build_args, dockerfile, image):
    # Set a current working directory
    src = ctx.host().directory(".")

    await (
        ctx.container()
            .build(context=src, dockerfile=dockerfile, build_args=build_args)
            .with_label("source.code.version.for.building", code_mapping_label)
            .with_label("repository.name", repo_name)
            .with_label("build.date", datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S_UTC"))
            .publish(address=f"{image}")
    )


if __name__ == "__main__":
    # Log in to the Azure Container Registry for each on-premises active in the configuration file
    for key, value in on_premises_config_data.items():
        if key in on_premises:
            # set the registry
            registry = value.get('registry')

            # Log in to the Azure Container Registry
            cli = get_default_cli()
            cli.invoke(['acr', 'login', '--name', registry])

    # Run the coroutine function to execute the compilation process for all on-premises
    run(compile_images_for_all_on_premises)
