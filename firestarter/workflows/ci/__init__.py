from .ci import CI
from .dagger_context import Context

def run(*, vars: dict, secrets: dict, config_file:str) -> None:
    context: Context = Context(vars, secrets)
    wf: CI = CI(config_file, context)
    wf.execute()

__all__ = [run]
