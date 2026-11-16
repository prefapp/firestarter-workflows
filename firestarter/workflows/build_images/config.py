import typing as t
from dataclasses import dataclass, field
from ruamel.yaml import YAML
import re
import uuid
from pathlib import Path
from jsonschema import ValidationError, SchemaError
from firestarter.common.preprocessor import ContextPathRule, interpolate_config_values
from firestarter.common.validations import validate_config_data
from firestarter.common.validations import validate_config_extra_tags
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

yaml = YAML(typ='safe')


def _is_flavor_secret_path(segments):
    return (
        len(segments) == 4
        and segments[0] in ('snapshots', 'releases')
        and segments[2] == 'secrets'
        and all(isinstance(segment, str) for segment in segments)
    )


BUILD_IMAGES_RESTRICTED_CONTEXTS = {
    'build_images_secrets': ContextPathRule(
        allowed=_is_flavor_secret_path,
        description="a flavor's 'secrets' mapping",
    ),
}


def load_config_values(source):
    """Protect expression tokens from YAML syntax without evaluating them."""
    prefix = f'firestarter_{uuid.uuid4().hex}_'
    expressions = {}

    def protect(match):
        token = f'{prefix}{len(expressions)}_'
        expressions[token] = match.group(0)
        return token

    data = yaml.load(re.sub(r'\{\{.*?\}\}', protect, source))

    def restore(value):
        if isinstance(value, dict):
            return {restore(key): restore(item) for key, item in value.items()}
        if isinstance(value, list):
            return [restore(item) for item in value]
        if isinstance(value, str):
            value = re.sub(prefix + r'\d+_', lambda match: expressions[match.group(0)], value)
            if prefix in value:
                raise ValueError(f"Failed to restore expression token in '{value}'")
            return value
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
    def from_yaml(cls: t.Type["Config"], config_file: str, type: str,
                  schema_file='schema.json', context=None, allow_undefined=False):
        sanitized_error = None
        try:
            with open(config_file, 'r') as file:
                raw_config = load_config_values(file.read())
            if context is not None:
                try:
                    raw_config = interpolate_config_values(
                        raw_config, context, allow_undefined, path=f'{config_file}:$',
                        restricted_contexts=BUILD_IMAGES_RESTRICTED_CONTEXTS)
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
            logger.error(
                "Invalid build images config '%s': %s",
                config_file,
                v_error.message,
            )
            sanitized_error = ValueError(
                f"Invalid build images config '{config_file}': {v_error.message}"
            )
        except SchemaError as s_error:
            logger.error(
                "Invalid build images schema '%s': %s",
                schema_file,
                s_error.message,
            )
            sanitized_error = ValueError(
                f"Invalid build images schema '{schema_file}': {s_error.message}"
            )

        if sanitized_error is not None:
            raise sanitized_error

        return config

    def to_dict(self):
        return {
            "images": {id: image.to_dict() for id, image in self.images.items()},
        }
