import argparse
import importlib
import logging
import os
import sys
import tomllib

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.environ.get("LOG_FILE", None)

logging.basicConfig(
    level=LOG_LEVEL,
    filename=LOG_FILE,
    format="[%(levelname)s][%(name)s] %(message)s",
)
logger = logging.getLogger(sys.argv[0])

def main():
    # Define command-line arguments
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('workflow', type=str, help='Name of the workflow to run')
    arg_parser.add_argument('--vars', type=str, help='Variables to pass to the workflow, in inline table toml format. Example: --vars=\'vars = { var1= "value1", var2= "value2"}\'')
    arg_parser.add_argument('--secrets', type=str, help='Secrets to pass to the workflow, in inline table toml format. Example: --secrets=\'secrets = { secret1= "foo", secret2= "bar"}\'')
    arg_parser.add_argument('--config_file', type=str, help='Optional configuration file for the workflow, located in the repository')
    args = arg_parser.parse_args()

    input_vars = os.environ.get("INPUT_VARS", None)
    input_secrets = os.environ.get("INPUT_SECRETS", None)
    input_config_file = os.environ.get("INPUT_CONFIG_FILE", None)

    vars = tomllib.loads(input_vars) if input_vars is not None else {}
    secrets = tomllib.loads(input_secrets) if input_secrets is not None else {}
    config_file = input_config_file if input_config_file is not None else args.config_file

    if args.vars:
      vars.update(tomllib.loads(args.vars).get("vars"))
      logger.debug(f"Inline vars: {vars}")
    if args.secrets:
      secrets.update(tomllib.loads(args.secrets).get("secrets"))
      logger.debug(f"Inline secrets: {secrets}")

    # Import the workflow module from the workflow name
    workflow = importlib.import_module(f"firestarter.workflows.{args.workflow}")
    logger.info(f"Running workflow {args.workflow} with vars {vars} and secrets {secrets}")
    result = workflow.run(
        vars=vars,
        secrets=secrets,
        config_file=config_file,
    )

    print(f"Results: {result}\n")
