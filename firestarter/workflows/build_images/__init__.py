from .build_images import BuildImages

def run(*, vars: dict, secrets: dict, config_file:str):
    try:
        wf = BuildImages(vars=vars, secrets=secrets, config_file=config_file)
        return wf.execute()
    except Exception as e:
        logger.error(f"::error title=Dagger Pipeline Failed::{e}")
        sys.exit(1)

__all__ = [run]
