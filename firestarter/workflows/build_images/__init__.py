import sys
import logging
from .build_images import BuildImages

def run(*, vars: dict, secrets: dict, config_file:str):
    try:
        wf = BuildImages(vars=vars, secrets=secrets, config_file=config_file)
        return wf.execute()
    except Exception as e:
        logging.exception("Fatal error encountered during BuildImages execution.")
        print(f"::error title=BuildImages Failure::{e}")
        sys.exit(1)

__all__ = [run]
