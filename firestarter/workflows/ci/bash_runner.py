"""This module contains functions for working with dagger containers."""
import tempfile
from typing import List, TextIO

WORKSPACE_PATH: str = "/workspace"

def create_script_from_commands(commands: List[str], temp_dir: str) -> None:
    """
    Builds a bash script from a list of commands.

    Args:
        commands: A list of strings representing commands.
        file: A file object where the script will be written.
    """
    # Create a file within the temporary directory
    temp_file: TextIO = tempfile.NamedTemporaryFile(dir=temp_dir, delete=False)

    script: str = "\n".join(["#!/bin/bash"] + commands)

    temp_file.write(script.encode())
    temp_file.close()

    return temp_file.name

async def exec_run_in_container(commands: List[str], container, dagger_client):
    """
    Executes commands in a container

    Parameters:
    commands (list): List of commands to execute in the container
    container (object): Dagger container instance
    dagger_client (object): Dagger client instance

    Returns:
    object: Dagger container instance
    """
    current_dir = dagger_client.host().directory(".")

    # Create a temporary directory
    container = (
        container
        # Set the entrypoint to bash -e to exit on error
        .with_entrypoint(["bash", "-e"])
    )

    if await container.workdir() != WORKSPACE_PATH:
        container = (
            container
            # Mount current dir
            .with_mounted_directory(WORKSPACE_PATH, current_dir)
            # Set as workdir
            .with_workdir(WORKSPACE_PATH)
        )

    # Create a temporary directory
    temp_dir: str = tempfile.mkdtemp()

    # Build the bash script
    file_name: str = create_script_from_commands(commands.split("\n"), temp_dir)

    # Get the id of the host current directory
    src = dagger_client.host().directory(temp_dir)

    container = (
        container
        # Mount the script directory
        .with_mounted_directory(temp_dir, src)
        # Make bash script executable
        .with_exec(["chmod", "+x", f"{file_name}"])
        # Execute the bash script
        .with_exec([f"{file_name}"])
    )

    return container
