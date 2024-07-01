from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from pathlib import Path

from pydantic import AfterValidator, BaseModel, Field, field_serializer
from typing_extensions import Annotated, Literal

from tach.constants import DEFAULT_EXCLUDE_PATHS, ROOT_MODULE_SENTINEL_TAG


class Config(BaseModel):
    model_config = {"extra": "forbid"}


class ModuleConfig(Config):
    """
    Configuration for a single module in a Tach project.

    Primarily responsible for declaring dependencies.
    """

    path: str
    depends_on: list[str] = Field(default_factory=list)
    strict: bool = False

    @property
    def mod_path(self) -> str:
        if self.path == ROOT_MODULE_SENTINEL_TAG:
            return "."
        return self.path


def validate_root_path(path: str) -> str:
    assert path == ROOT_MODULE_SENTINEL_TAG
    return path


class RootModuleConfig(ModuleConfig):
    """
    Special-case schema for the implicit root module configuration.
    """

    path: Annotated[str, AfterValidator(validate_root_path)] = ROOT_MODULE_SENTINEL_TAG


@dataclass
class UnusedDependencies:
    path: str
    dependencies: list[str]


class CacheConfig(Config):
    """
    Configuration affecting Tach's caching.

    Responsible for configuring the cache backend, and adjusting the dependencies which should affect cache retrieval.
    """

    backend: Literal["local"] = "local"
    file_dependencies: list[str] = Field(default_factory=list)
    env_dependencies: list[str] = Field(default_factory=list)


class ProjectConfig(Config):
    """
    Central configuration object for a project using Tach.

    Controls which modules are defined, their dependencies, as well as global tool-related configuration.
    """

    modules: list[ModuleConfig] = Field(default_factory=list)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    exclude: list[str] | None = Field(
        default_factory=lambda: copy(DEFAULT_EXCLUDE_PATHS)
    )
    source_root: Path = Field(default_factory=lambda: Path("."))
    exact: bool = False
    disable_logging: bool = False
    ignore_type_checking_imports: bool = True

    @field_serializer("source_root")
    def serialize_source_root(self, source_root: Path, _) -> str:
        return str(source_root)

    @property
    def module_paths(self) -> list[str]:
        return [module.path for module in self.modules]

    def set_modules(self, module_paths: list[str]) -> None:
        new_modules: list[ModuleConfig] = []
        new_module_paths = set(module_paths)
        original_modules_by_path = {
            module_config.path: module_config for module_config in self.modules
        }
        for new_module_path in new_module_paths:
            if new_module_path in original_modules_by_path:
                original_module = original_modules_by_path[new_module_path]
                original_module.depends_on = [
                    dep for dep in original_module.depends_on if dep in new_module_paths
                ]
                new_modules.append(original_module)
            else:
                new_modules.append(ModuleConfig(path=new_module_path))

        self.modules = new_modules

    def dependencies_for_module(self, module: str) -> list[str]:
        return next(
            (mod.depends_on for mod in self.modules if mod.path == module),
            [],  # type: ignore
        )

    def add_dependency_to_module(self, module: str, dependency: str):
        current_module_config = next(
            (
                module_config
                for module_config in self.modules
                if module_config.path == module
            ),
            None,
        )
        if not current_module_config:
            # No configuration exists for tag, add default config with this dependency
            self.modules.append(ModuleConfig(path=module, depends_on=[dependency]))
        else:
            # Config already exists, set the union of existing dependencies and new ones
            new_dependencies = set(current_module_config.depends_on) | {dependency}
            current_module_config.depends_on = list(new_dependencies)

    def compare_dependencies(
        self, other_config: ProjectConfig
    ) -> list[UnusedDependencies]:
        all_unused_dependencies: list[UnusedDependencies] = []
        own_module_paths = set(module.path for module in self.modules)
        for module_config in other_config.modules:
            if module_config.path not in own_module_paths:
                all_unused_dependencies.append(
                    UnusedDependencies(
                        path=module_config.path, dependencies=module_config.depends_on
                    )
                )
                continue
            own_module_dependencies = set(
                self.dependencies_for_module(module=module_config.path)
            )
            extra_dependencies = set(module_config.depends_on) - own_module_dependencies
            if extra_dependencies:
                all_unused_dependencies.append(
                    UnusedDependencies(
                        path=module_config.path,
                        dependencies=list(extra_dependencies),
                    )
                )

        return all_unused_dependencies
