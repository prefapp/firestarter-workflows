import typing as t
from dataclasses import dataclass, field
from ruamel.yaml import YAML
import re
import uuid
from pathlib import Path
from jsonschema import ValidationError, SchemaError
from firestarter.common.preprocessor import interpolate_config_values
from firestarter.common.validations import validate_config_data
from firestarter.common.validations import validate_config_extra_tags
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

yaml = YAML(typ='safe')


def load_config_values(source):
    """Protect expression tokens from YAML syntax without evaluating them."""
    prefix = f'firestarter_{uuid.uuid4().hex}_'
    expressions = {}

    def protect(match):
        token = f'{prefix}{len(expressions)}'
        expressions[token] = match.group(0)
        return token

    data = yaml.load(re.sub(r'\{\{.*?\}\}', protect, source))

    def restore(value):
        if isinstance(value, dict):
            return {restore(key): restore(item) for key, item in value.items()}
        if isinstance(value, list):
            return [restore(item) for item in value]
        if isinstance(value, str):
            return re.sub(prefix + r'\d+', lambda match: expressions[match.group(0)], value)
        return value

    return restore(data)

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
    platforms: list = field(default_factory=lambda: ["linux/amd64"])

    @classmethod
    def from_dict(cls: t.Type["Image"], obj: dict):
        return cls(
            auto=obj.get("auto"),
            build_always=obj.get("build_always"),
            registry=obj.get("registry"),
            extra_registries=obj.get("extra_registries"),
            build_args=obj.get("build_args"),
            extra_tags=obj.get("extra_tags", []),
            platforms=obj.get("platforms", ["linux/amd64"]),
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
            "platforms": self.platforms,
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
    def from_yaml(cls: t.Type["Config"], config_file: str, type: str, secrets: dict,
                  schema_file='schema.json', context=None, allow_undefined=False):
        try:
            with open(config_file, 'r') as file:
                raw_config = load_config_values(file.read())
            if context is not None:
                try:
                    raw_config = interpolate_config_values(
                        raw_config, context, allow_undefined, path=f'{config_file}:$')
                except ValueError as error:
                    hint = ''
                    if str(error).startswith('Unknown context '):
                        supported = " and ".join(f"'{name}'" for name in context)
                        description = 'context is' if len(context) == 1 else 'contexts are'
                        hint = f'; only the {supported} {description} supported'
                    raise ValueError(f"{error} in config '{config_file}'{hint}") from error
            validate_config_data(raw_config, schema_file)
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
        return config

    def to_dict(self):
        return {
            "images": {id: image.to_dict() for id, image in self.images.items()},
        }
