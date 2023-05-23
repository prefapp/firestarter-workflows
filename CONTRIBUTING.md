# How to contribute

## Creating a new workflow

To create a new workflow follow these steps:

1. Create a new folder in the `workflows` directory.
2. Add a `README.md` file to the new folder. This file should contain a description of the workflow.
3. Add an `__init__.py` file to the new folder. This file should export a function called `run` with the following signature:
    
    `def run(vars:dict=None, secrets:dict=None, config_file:str=None) -> Integer`.


To test your workflow locally follow the below steps (check the [example repository](https://github.com/prefapp/test-repo-rundagger) for more details):
1. Create a new folder.
2. Create a `pyproject.toml` using `poetry init`.
3. Update the `pyproject.toml` namespace to "firestarter":
    ```toml
    [tool.poetry]
    name = "firestarter"
    ```
4. Create the folder `/firestarter/workflows` and add your workflow folder inside.
5. Execute the workflow using `poetry run firestarter local` (use `poetry run firestarter -h` for more details).

## Contributing to cli

To make changes in the cli and test it locally you need to update the `pyproject.toml` to update the dependencies.

This can be done in the following ways:

* Use a git branch instead of main ([docs](https://python-poetry.org/docs/dependency-specification/#git-dependencies)):
    ```toml
    [tool.poetry.dependencies]
    python = "^3.11"
    firestarter-workflows = {git = "https://github.com/prefapp/firestarter-workflows", branch = "fix/new-bug"}
    ``` 
* Use the local directory files ([docs](https://python-poetry.org/docs/dependency-specification/#path-dependencies)):
    ```toml
    [tool.poetry.dependencies]
    python = "^3.11"
    firestarter-workflows = {path = "../firestarter-workflows"}
    ```
> Remember to update the dependencies when doing so (`poetry update firestarter-workflows`).
