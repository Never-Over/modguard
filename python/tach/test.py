from __future__ import annotations

from copy import copy
from typing import TYPE_CHECKING, Any

from tach import filesystem as fs
from tach.errors import TachError, TachSetupError
from tach.extension import get_project_imports
from tach.filesystem.git_ops import get_changed_files
from tach.parsing import build_module_tree

if TYPE_CHECKING:
    from pathlib import Path

    from tach.core import ModuleConfig, ModuleTree, ProjectConfig


def build_module_consumer_map(modules: list[ModuleConfig]) -> dict[str, list[str]]:
    consumer_map: dict[str, list[str]] = {}
    for module in modules:
        for dependency in module.depends_on:
            if dependency in consumer_map:
                consumer_map[dependency].append(module.mod_path)
            else:
                consumer_map[dependency] = [module.mod_path]
    return consumer_map


def get_changed_module_paths(
    project_root: Path, project_config: ProjectConfig, changed_files: list[Path]
) -> list[str]:
    source_root = project_root / project_config.source_root
    changed_module_paths = [
        fs.file_to_module_path(
            source_root=source_root, file_path=changed_file.resolve()
        )
        for changed_file in changed_files
        if source_root in changed_file.resolve().parents
    ]

    return changed_module_paths


def find_affected_modules(
    root_module_path: str,
    module_consumers: dict[str, list[str]],
    known_affected_modules: set[str],
) -> set[str]:
    if root_module_path not in module_consumers:
        return known_affected_modules
    for consumer in module_consumers[root_module_path]:
        # avoid recursing on modules we have already seen to prevent infinite cycles
        if consumer not in known_affected_modules:
            known_affected_modules.add(consumer)
            known_affected_modules |= find_affected_modules(
                consumer,
                module_consumers=module_consumers,
                known_affected_modules=known_affected_modules,
            )
    return known_affected_modules


def get_affected_modules(
    project_root: Path,
    project_config: ProjectConfig,
    changed_files: list[Path],
    module_tree: ModuleTree,
) -> set[str]:
    changed_module_paths = get_changed_module_paths(
        project_root, project_config, changed_files
    )
    affected_modules: set[str] = set()
    for changed_mod_path in changed_module_paths:
        nearest_module = module_tree.find_nearest(changed_mod_path)
        if nearest_module is None:
            raise TachError(
                f"Could not find module containing path: {changed_mod_path}"
            )
        affected_modules.add(nearest_module.full_path)

    module_consumers = build_module_consumer_map(project_config.modules)
    for module in list(affected_modules):
        find_affected_modules(
            module,
            module_consumers=module_consumers,
            known_affected_modules=affected_modules,
        )
    return affected_modules


def run_affected_tests(
    project_root: Path,
    project_config: ProjectConfig,
    head: str,
    base: str,
    pytest_args: list[Any] | None = None,
) -> int:
    try:
        import pytest  # type: ignore  # noqa: F401
    except ImportError:
        raise TachSetupError("Cannot run tests, could not find 'pytest'.")

    class TachPytestPlugin:
        def __init__(
            self,
            project_root: Path,
            source_root: Path,
            module_tree: ModuleTree,
            affected_modules: set[str],
        ):
            self.project_root = project_root
            self.source_root = source_root
            self.module_tree = module_tree
            self.affected_modules = affected_modules
            self.removed_test_paths: set[Path] = set()
            self.num_removed_items: int = 0

        def pytest_collection_modifyitems(
            self,
            session: pytest.Session,
            config: pytest.Config,
            items: list[pytest.Item],
        ):
            seen: set[Path] = set()
            for item in copy(items):
                if not item.path:
                    continue
                if item.path in self.removed_test_paths:
                    self.num_removed_items += 1
                    items.remove(item)
                    continue
                if item.path in seen:
                    continue
                project_imports = get_project_imports(
                    project_root=str(self.project_root),
                    source_root=str(self.source_root),
                    file_path=str(item.path.resolve()),
                    ignore_type_checking_imports=True,
                )
                for mod_path, _ in project_imports:
                    nearest_module = self.module_tree.find_nearest(mod_path)
                    if not nearest_module:
                        continue
                    if nearest_module.full_path in self.affected_modules:
                        # We can break early without any modifications, since we know this file path is affected
                        break
                else:
                    # If none of the project imports in the test are affected, we can skip all tests in the file path
                    self.num_removed_items += 1
                    items.remove(item)
                    self.removed_test_paths.add(item.path)
                seen.add(item.path)

        def pytest_report_collectionfinish(
            self,
            config: pytest.Config,
            start_path: Path,
            startdir: Any,
            items: list[pytest.Item],
        ) -> str | list[str]:
            return [
                f"[Tach] Skipped {len(self.removed_test_paths)} test file{'s' if len(self.removed_test_paths) > 1 else ''}"
                f" ({self.num_removed_items} tests)"
                " since they were unaffected by current changes.",
                *(
                    f"[Tach] > Skipped '{test_path}'"
                    for test_path in self.removed_test_paths
                ),
            ]

    absolute_source_root = project_root / project_config.source_root

    module_validation_result = fs.validate_project_modules(
        source_root=absolute_source_root, modules=project_config.modules
    )
    # TODO: log warning
    for module in module_validation_result.invalid_modules:
        print(f"Module '{module.path}' not found. It will be ignored.")

    module_tree = build_module_tree(
        source_root=absolute_source_root,
        modules=module_validation_result.valid_modules,
    )

    # These paths come from git output, which means they are relative to cwd
    changed_files = get_changed_files(project_root, head=head, base=base)
    affected_module_paths = get_affected_modules(
        project_root,
        project_config,
        changed_files=changed_files,
        module_tree=module_tree,
    )
    pytest_plugin = TachPytestPlugin(
        project_root=project_root,
        source_root=project_config.source_root,
        module_tree=module_tree,
        affected_modules=affected_module_paths,
    )

    return pytest.main(pytest_args, plugins=[pytest_plugin])


__all__ = ["run_affected_tests"]
