import typing as t
from dataclasses import dataclass, field

import yaml

@dataclass
class Image:
    registry: str
    repository: str
    build_args: dict = field(default_factory=dict)
    dockerfile: str = field(default="Dockerfile")

    @classmethod
    def from_dict(cls: t.Type["Image"], obj: dict):
        return cls(
            registry=obj.get("registry"),
            repository=obj.get("repository"),
            build_args=obj.get("build_args"),
            dockerfile=obj.get("dockerfile"),
        )

    def to_dict(self):
        return {
            "registry": self.registry,
            "repository": self.repository,
            "build_args": self.build_args,
            "dockerfile": self.dockerfile,
        }

@dataclass
class Config:
    images: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls: t.Type["Config"], obj: dict):
        return cls(
            images={id: Image.from_dict(image) for id, image in obj.get("images", {}).items()}
            )

    @classmethod
    def from_yaml(cls: t.Type["Config"], file: str):
        with open(file, "r") as f:
            raw_config = yaml.safe_load(f)
        return cls.from_dict(raw_config)

    def to_dict(self):
        return {
            "images": {id: image.to_dict() for id, image in self.images.items()},
        }
