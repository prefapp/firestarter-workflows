import typing as t
from dataclasses import dataclass, field
from ruamel.yaml import YAML
import re
import json
from pathlib import Path
from jsonschema import ValidationError, SchemaError
from firestarter.common.validations import validate_config
from firestarter.common.validations import validate_extra_tags
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

yaml = YAML(typ='safe')

@dataclass
class Image:
    auto: bool = field(default=False)
    build_always: bool = field(default=True)
    registry: dict = field(default_factory=dict)
    extra_registries: dict = field(default_factory=dict)
    build_args: dict = field(default_factory=dict)
    secrets: dict = field(default_factory=dict)
    dockerfile: str = field(default="Dockerfile")
    extra_tags: list = field(default_factory=list)

    @classmethod
    def from_dict(cls: t.Type["Image"], obj: dict):
        return cls(
            auto=obj.get("auto"),
            build_always=obj.get("build_always"),
            registry=obj.get("registry"),
            extra_registries=obj.get("extra_registries"),
            build_args=obj.get("build_args"),
            extra_tags=obj.get("extra_tags", []),
            secrets=obj.get("secrets"),
            dockerfile=obj.get("dockerfile"),
        )

    def to_dict(self):
        return {
            "auto": self.auto,
            "build_always": self.build_always,
            "registry": self.registry,
            "extra_registries": self.extra_registries,
            "build_args": self.build_args,
            "extra_tags": self.extra_tags,
            "secrets": self.secrets,
            "dockerfile": self.dockerfile,
        }

@dataclass
class Config:
    images: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls: t.Type["Config"], obj: dict):
        images = {}
        for id, image in obj.items():
            if not Path(image.get("dockerfile")).is_file():
                raise ValueError(f"File '{image.get('dockerfile')}' not found for flavor '{id}'")
            images[id] = Image.from_dict(image)

        return cls(
            images=images
        )



    @classmethod
    def from_yaml(cls: t.Type["Config"], config_file: str, type: str, secrets: dict, schema_file='schema.json'):
        try:
            raw_config = validate_config(config_file, schema_file)
            validate_config_extra_tags(raw_config)
            logger.info(f"The config file '{config_file}' is valid")
            config = cls.from_dict(raw_config[type])
        except FileNotFoundError as fnf_error:
            logger.error(f"File not found {fnf_error}")
            raise
        except ValidationError as v_error:
            logger.error(f"Validate error {v_error.message}")
            raise
        except SchemaError as s_error:
            logger.error(f"Error in schema {s_error.message}")
            raise
        else:
            replace_secrets(config.to_dict(), secrets)
            logger.info("The secrets has been replaced correctly in the set up")

        return config

    def to_dict(self):
        return {
            "images": {id: image.to_dict() for id, image in self.images.items()},
        }


def replace_secrets(data, secrets) -> dict:
    # check first if dict is a dictionary
    for key, val in data.items():
        if isinstance(val, dict):
            replace_secrets(val, secrets)
        elif isinstance(val, str):
            m = re.search(
                r'^\{\{\ssecrets\.([a-zA-Z][a-zA-Z0-9-_]+)\s\}\}$', val)
            if m:
                data[key] = secrets[m.group(1)]
    return data
