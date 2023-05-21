from .build_images import BuildImages

def run(*, vars: dict, secrets: dict, config_file:str):
    wf = BuildImages(vars=vars, secrets=secrets, config_file=config_file)
    wf.execute()

__all__ = [run]
