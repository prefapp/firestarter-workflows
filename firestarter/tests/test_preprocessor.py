from firestarter.common.preprocessor import PreProcessor
import os
from ruamel.yaml import YAML
import pytest
from types import SimpleNamespace
from firestarter.workflows.ci.task_manager import TaskManager

yaml = YAML(typ='safe')


def load_yaml(file_path: str) -> dict:
    with open(file_path, "r") as f:
        return yaml.load(f)

def process_env_var(var_name: str) -> str:
    if not var_name in FAKE_OS_ENVIRON:
        raise ValueError(f'{var_name} not found in fake sys environment')

    return FAKE_OS_ENVIRON[var_name]


FAKE_OS_ENVIRON: dict = {
    "SHELL": "/bin/fake_shell",
    "PATH": "fake_path;fake_path2;pake_fath",
}

DEFAULT_PREPROCESS_DICT: dict = {
    "vars": lambda v: f"VAR_{v}",
    "secrets": lambda s: f"SECRET_{s}",
    "env": process_env_var,
}


def process_file(
    file_path: str, preprocess_dict: dict = DEFAULT_PREPROCESS_DICT
) -> dict:
    pp: PreProcessor = PreProcessor(load_yaml(os.path.join(
        os.path.dirname(__file__), file_path
    )))

    return pp.preprocess(preprocess_dict)


def test_parser() -> None:
    result: dict = process_file("fixtures/preprocess_workflow.yaml")

    assert result.get("a", {}).get("value", "") == "SECRET_SECRET1"
    assert result.get("b", [{}])[0].get("name", "") == process_env_var("SHELL")
    assert result.get("b", [{}])[0].get("value", "") == "VAR_VALUE"

def test_unknown_context_error() -> None:
    with pytest.raises(ValueError, match="Unknown context"):
        process_file("fixtures/preprocess_workflow_error.yaml")

def test_var_name_not_in_context_error() -> None:
    preprocess_dict: dict = {
        "vars": lambda v: f"VAR_{v}",
        "inexistent": lambda s: f"SECRET_{s}",
        "env": process_env_var,
    }
    with pytest.raises(ValueError, match="not found in fake sys environment"):
        process_file("fixtures/preprocess_workflow_error.yaml", preprocess_dict)


def test_ci_keeps_all_three_contexts(tmp_path, monkeypatch):
    monkeypatch.setenv('CI_VALUE', 'env-value')
    path = tmp_path / 'ci.yaml'
    path.write_text('''
image: ${{ vars.IMAGE }}
version: "1"
vars:
  ENV_VALUE: "prefix-${{ env.CI_VALUE }}"
  SECRET_VALUE: '${{ secrets.TOKEN }}'
tasks: []
''')
    manager = TaskManager()
    manager.context = SimpleNamespace(vars={'IMAGE': 'alpine'}, secrets={'TOKEN': 'token-value'})
    manager.load(str(path), '../workflows/ci/schema.json')
    assert manager.context.default_image == 'alpine'
    assert manager.context.default_env == {
        'ENV_VALUE': 'prefix-env-value', 'SECRET_VALUE': 'token-value',
    }
