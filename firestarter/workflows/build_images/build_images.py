import logging
from firestarter.common.firestarter_workflow import FirestarterWorkflow

logger = logging.getLogger(__name__)


class BuildImages(FirestarterWorkflow):
    def execute(self):
        print(f"Eiqui")
