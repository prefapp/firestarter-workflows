"""This module contains functions for working with dagger containers."""
import tempfile
from typing import List, TextIO

def create_script_from_commands(commands: List[str], file: TextIO) -> None:
    """Builds a bash script from a list of commands.

    Args:
        commands: A list of strings representing commands.
        file: A file object where the script will be written.
    """
    script: str = "\n".join(["#!/bin/bash"] + commands)

    file.write(script.encode())
    file.close()

def exec_run_in_container(commands: List[str], container, dagger_client):
    """
    Executes commands in a container

    Parameters:
    commands (list): List of commands to execute in the container
    container (object): Dagger container instance
    dagger_client (object): Dagger client instance

    Returns:
    object: Dagger container instance
    """

    # Create a temporary directory
    container = (
        container
        # Set the entrypoint to bash -e to exit on error
        .with_entrypoint(["bash", "-e"])
    )

    # Create a temporary directory
    temp_dir: str = tempfile.mkdtemp()

    # Create a file within the temporary directory
    temp_file: TextIO = tempfile.NamedTemporaryFile(dir=temp_dir, delete=False)

    # Build the bash script
    create_script_from_commands(commands.split("\n"), temp_file)

    # Get the id of the host current directory
    src = dagger_client.host().directory(temp_dir)

    container = (
        container
        # Mount the script directory
        .with_mounted_directory(temp_dir, src)
        # Execute the bash script
        .exec([f"{temp_file.name}"])
    )

    return container
