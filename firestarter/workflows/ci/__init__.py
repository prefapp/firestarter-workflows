from .ci import CI
from firestarter.common.dagger_context import Context

def run(*, vars: dict, secrets: dict, config_file:str) -> None:
    context: Context = Context()
    wf: CI = CI(config_file, context)
    wf.execute()

__all__ = [run]
