import sys
import logging
from .build_images import BuildImages

logger = logging.getLogger(__name__)

def run(*, vars: dict, secrets: dict, additional_build_args: dict, config_file:str):
    try:
        wf = BuildImages(
            vars=vars,
            secrets=secrets,
            additional_build_args=additional_build_args,
            config_file=config_file
        )
        return wf.execute()
    except Exception as e:
        logger.exception("Fatal error encountered during BuildImages execution.")
        print(f"::error title=BuildImages Failure::{e}")
        sys.exit(1)

__all__ = [run]
