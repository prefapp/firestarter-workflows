from firestarter.common.preprocessor import PreProcessor
import os
import yaml
import pytest

FAKE_OS_ENVIRON: dict = {
    "SHELL": "/bin/fake_shell",
    "PATH": "fake_path;fake_path2;pake_fath",
}


def load_yaml(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

def process_env_var(var_name: str) -> str:
    if not var_name in FAKE_OS_ENVIRON:
        raise ValueError(f'{var_name} not found in fake sys environment')

    return FAKE_OS_ENVIRON[var_name]


def process_file(file_path: str) -> str:
    pp: PreProcessor = PreProcessor(load_yaml(os.path.join(
        os.path.dirname(__file__), file_path
    )))

    return pp.preprocess({
        "vars": lambda v: f"VAR_{v}",
        "secrets": lambda s: f"SECRET_{s}",
        "env": process_env_var,
    })


def test_parser() -> None:
    result: dict = yaml.load(
        process_file("fixtures/preprocess_workflow.yaml"), Loader=yaml.Loader
    )

    assert result.get("a", {}).get("value", "") == "SECRET_SECRET1"
    assert result.get("b", {})[0].get("name", "") == process_env_var("SHELL")
    assert result.get("b", {})[0].get("value", "") == "VAR_VALUE"

def test_error() -> None:
    with pytest.raises(ValueError, match="Unknown context"):
        result: dict = yaml.load(
            process_file("fixtures/preprocess_workflow_error.yaml"),
            Loader=yaml.Loader,
        )

