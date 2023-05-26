from firestarter.common.preprocessor import PreProcessor
import os
import yaml
import pytest

def load_yaml(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

def process_file(file_path: str) -> str:
    pp: PreProcessor = PreProcessor(load_yaml(os.path.join(
        os.path.dirname(__file__), file_path
    )))

    return pp.preprocess({
        "resolve_var": lambda v: f"VAR_{v}",
        "resolve_secret": lambda s: f"VAR_{s}",
    })


def test_parser() -> None:
    result: dict = yaml.load(
        process_file("fixtures/preprocess_workflow.yaml"), Loader=yaml.Loader
    )

    assert result.get("a", {}).get("value", "") == "VAR_SECRET1"
    assert result.get("b", {})[0].get("name", "") == os.environ["SHELL"]
    assert result.get("b", {})[0].get("value", "") == "VAR_VALUE"

def test_error() -> None:
    with pytest.raises(ValueError, match="Unknown context"):
        result: dict = yaml.load(
            process_file("fixtures/preprocess_workflow_error.yaml"),
            Loader=yaml.Loader,
        )

