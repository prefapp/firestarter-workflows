import typing as t
from dataclasses import dataclass, field

import yaml

@dataclass
class Image:
    build_always: bool = field(default=True)
    extra_registries: dict = field(default_factory=dict)
    build_args: dict = field(default_factory=dict)
    secrets: dict = field(default_factory=dict)
    dockerfile: str = field(default="Dockerfile")

    @classmethod
    def from_dict(cls: t.Type["Image"], obj: dict):
        return cls(
            build_always=obj.get("build_always"),
            extra_registries=obj.get("extra_registries"),
            build_args=obj.get("build_args"),
            secrets=obj.get("secrets"),
            dockerfile=obj.get("dockerfile"),
        )

    def to_dict(self):
        return {
            "build_always": self.build_always,
            "extra_registries": self.extra_registries,
            "build_args": self.build_args,
            "secrets": self.secrets,
            "dockerfile": self.dockerfile,
        }

@dataclass
class Config:
    images: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls: t.Type["Config"], obj: dict):
        return cls(
            images={id: Image.from_dict(image) for id, image in obj.items()}
        )

    @classmethod
    def from_yaml(cls: t.Type["Config"], file: str, type: str):
        with open(file, "r") as f:
            raw_config = yaml.safe_load(f)
        config = cls.from_dict(raw_config[type])
        return config

    def to_dict(self):
        return {
            "images": {id: image.to_dict() for id, image in self.images.items()},
        }
