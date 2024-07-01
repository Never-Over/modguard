from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from tach.core.config import ModuleConfig, ProjectConfig, RootModuleConfig
from tach.core.modules import ModuleNode, ModuleTree
from tach.test import get_affected_modules, get_changed_module_paths

# Module-related data in fixtures was auto-generated from the 'tach' codebase
# June 28, 2024


@pytest.fixture
def modules() -> list[ModuleConfig]:
    return [
        ModuleConfig(path="tach", depends_on=[], strict=True),
        ModuleConfig(path="tach.__main__", depends_on=["tach.start"], strict=True),
        ModuleConfig(
            path="tach.cache", depends_on=["tach", "tach.filesystem"], strict=True
        ),
        ModuleConfig(
            path="tach.check",
            depends_on=["tach.errors", "tach.filesystem", "tach.parsing"],
            strict=True,
        ),
        ModuleConfig(
            path="tach.cli",
            depends_on=[
                "tach",
                "tach.cache",
                "tach.check",
                "tach.colors",
                "tach.constants",
                "tach.core",
                "tach.errors",
                "tach.filesystem",
                "tach.logging",
                "tach.mod",
                "tach.parsing",
                "tach.report",
                "tach.show",
                "tach.sync",
                "tach.test",
            ],
            strict=True,
        ),
        ModuleConfig(path="tach.colors", depends_on=[], strict=True),
        ModuleConfig(path="tach.constants", depends_on=[], strict=True),
        ModuleConfig(path="tach.core", depends_on=["tach.constants"], strict=True),
        ModuleConfig(path="tach.errors", depends_on=[], strict=True),
        ModuleConfig(
            path="tach.filesystem",
            depends_on=[
                "tach.colors",
                "tach.constants",
                "tach.core",
                "tach.errors",
                "tach.hooks",
            ],
            strict=True,
        ),
        ModuleConfig(
            path="tach.filesystem.git_ops", depends_on=["tach.errors"], strict=True
        ),
        ModuleConfig(path="tach.hooks", depends_on=["tach.constants"], strict=True),
        ModuleConfig(
            path="tach.interactive",
            depends_on=["tach.errors", "tach.filesystem"],
            strict=True,
        ),
        ModuleConfig(
            path="tach.logging",
            depends_on=["tach", "tach.cache", "tach.parsing"],
            strict=True,
        ),
        ModuleConfig(
            path="tach.mod",
            depends_on=[
                "tach.colors",
                "tach.constants",
                "tach.errors",
                "tach.filesystem",
                "tach.interactive",
                "tach.parsing",
            ],
            strict=True,
        ),
        ModuleConfig(
            path="tach.parsing",
            depends_on=["tach.constants", "tach.core", "tach.filesystem"],
            strict=True,
        ),
        ModuleConfig(path="tach.report", depends_on=["tach.errors"], strict=True),
        ModuleConfig(path="tach.show", depends_on=[], strict=True),
        ModuleConfig(path="tach.start", depends_on=["tach.cli"], strict=True),
        ModuleConfig(
            path="tach.sync",
            depends_on=["tach.check", "tach.errors", "tach.filesystem", "tach.parsing"],
            strict=True,
        ),
        ModuleConfig(
            path="tach.test",
            depends_on=[
                "tach.errors",
                "tach.filesystem",
                "tach.filesystem.git_ops",
                "tach.parsing",
            ],
            strict=False,
        ),
    ]


@pytest.fixture
def module_tree() -> ModuleTree:
    return ModuleTree(
        root=ModuleNode(
            is_end_of_path=True,
            full_path=".",
            config=RootModuleConfig(path="<root>", depends_on=[], strict=False),
            interface_members=[],
            children={
                "tach": ModuleNode(
                    is_end_of_path=True,
                    full_path="tach",
                    config=ModuleConfig(path="tach", depends_on=[], strict=True),
                    interface_members=["__version__"],
                    children={
                        "__main__": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.__main__",
                            config=ModuleConfig(
                                path="tach.__main__",
                                depends_on=["tach.start"],
                                strict=True,
                            ),
                            interface_members=[],
                            children={},
                        ),
                        "cache": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.cache",
                            config=ModuleConfig(
                                path="tach.cache",
                                depends_on=["tach", "tach.filesystem"],
                                strict=True,
                            ),
                            interface_members=[
                                "get_uid",
                                "update_latest_version",
                                "get_latest_version",
                            ],
                            children={},
                        ),
                        "check": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.check",
                            config=ModuleConfig(
                                path="tach.check",
                                depends_on=[
                                    "tach.errors",
                                    "tach.filesystem",
                                    "tach.parsing",
                                ],
                                strict=True,
                            ),
                            interface_members=["BoundaryError", "check"],
                            children={},
                        ),
                        "cli": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.cli",
                            config=ModuleConfig(
                                path="tach.cli",
                                depends_on=[
                                    "tach",
                                    "tach.cache",
                                    "tach.check",
                                    "tach.colors",
                                    "tach.constants",
                                    "tach.core",
                                    "tach.errors",
                                    "tach.filesystem",
                                    "tach.logging",
                                    "tach.mod",
                                    "tach.parsing",
                                    "tach.report",
                                    "tach.show",
                                    "tach.sync",
                                    "tach.test",
                                ],
                                strict=True,
                            ),
                            interface_members=["main"],
                            children={},
                        ),
                        "colors": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.colors",
                            config=ModuleConfig(
                                path="tach.colors", depends_on=[], strict=True
                            ),
                            interface_members=["BCOLORS"],
                            children={},
                        ),
                        "constants": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.constants",
                            config=ModuleConfig(
                                path="tach.constants", depends_on=[], strict=True
                            ),
                            interface_members=[
                                "PACKAGE_NAME",
                                "TOOL_NAME",
                                "CONFIG_FILE_NAME",
                                "PACKAGE_FILE_NAME",
                                "ROOT_MODULE_SENTINEL_TAG",
                                "DEFAULT_EXCLUDE_PATHS",
                            ],
                            children={},
                        ),
                        "core": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.core",
                            config=ModuleConfig(
                                path="tach.core",
                                depends_on=["tach.constants"],
                                strict=True,
                            ),
                            interface_members=[
                                "ProjectConfig",
                                "ModuleConfig",
                                "ModuleNode",
                                "ModuleTree",
                                "UnusedDependencies",
                            ],
                            children={},
                        ),
                        "errors": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.errors",
                            config=ModuleConfig(
                                path="tach.errors", depends_on=[], strict=True
                            ),
                            interface_members=[
                                "TachError",
                                "TachParseError",
                                "TachSetupError",
                            ],
                            children={},
                        ),
                        "filesystem": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.filesystem",
                            config=ModuleConfig(
                                path="tach.filesystem",
                                depends_on=[
                                    "tach.colors",
                                    "tach.constants",
                                    "tach.core",
                                    "tach.errors",
                                    "tach.hooks",
                                ],
                                strict=True,
                            ),
                            interface_members=[
                                "get_cwd",
                                "chdir",
                                "canonical",
                                "read_file",
                                "write_file",
                                "delete_file",
                                "parse_ast",
                                "walk",
                                "walk_pyfiles",
                                "file_to_module_path",
                                "module_to_file_path_no_members",
                                "module_to_pyfile_or_dir_path",
                                "get_project_config_path",
                                "find_project_config_root",
                                "install_pre_commit",
                                "validate_project_modules",
                                "ProjectModuleValidationResult",
                            ],
                            children={
                                "git_ops": ModuleNode(
                                    is_end_of_path=True,
                                    full_path="tach.filesystem.git_ops",
                                    config=ModuleConfig(
                                        path="tach.filesystem.git_ops",
                                        depends_on=["tach.errors"],
                                        strict=True,
                                    ),
                                    interface_members=["get_changed_files"],
                                    children={},
                                )
                            },
                        ),
                        "hooks": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.hooks",
                            config=ModuleConfig(
                                path="tach.hooks",
                                depends_on=["tach.constants"],
                                strict=True,
                            ),
                            interface_members=["build_pre_commit_hook_content"],
                            children={},
                        ),
                        "interactive": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.interactive",
                            config=ModuleConfig(
                                path="tach.interactive",
                                depends_on=["tach.errors", "tach.filesystem"],
                                strict=True,
                            ),
                            interface_members=[
                                "get_selected_modules_interactive",
                                "InteractiveModuleConfiguration",
                            ],
                            children={},
                        ),
                        "logging": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.logging",
                            config=ModuleConfig(
                                path="tach.logging",
                                depends_on=["tach", "tach.cache", "tach.parsing"],
                                strict=True,
                            ),
                            interface_members=["logger", "LogDataModel"],
                            children={},
                        ),
                        "mod": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.mod",
                            config=ModuleConfig(
                                path="tach.mod",
                                depends_on=[
                                    "tach.colors",
                                    "tach.constants",
                                    "tach.errors",
                                    "tach.filesystem",
                                    "tach.interactive",
                                    "tach.parsing",
                                ],
                                strict=True,
                            ),
                            interface_members=["mod_edit_interactive"],
                            children={},
                        ),
                        "parsing": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.parsing",
                            config=ModuleConfig(
                                path="tach.parsing",
                                depends_on=[
                                    "tach.constants",
                                    "tach.core",
                                    "tach.filesystem",
                                ],
                                strict=True,
                            ),
                            interface_members=[
                                "parse_project_config",
                                "dump_project_config_to_yaml",
                                "parse_interface_members",
                                "build_module_tree",
                            ],
                            children={},
                        ),
                        "report": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.report",
                            config=ModuleConfig(
                                path="tach.report",
                                depends_on=["tach.errors"],
                                strict=True,
                            ),
                            interface_members=["report"],
                            children={},
                        ),
                        "show": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.show",
                            config=ModuleConfig(
                                path="tach.show", depends_on=[], strict=True
                            ),
                            interface_members=["generate_show_url"],
                            children={},
                        ),
                        "start": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.start",
                            config=ModuleConfig(
                                path="tach.start", depends_on=["tach.cli"], strict=True
                            ),
                            interface_members=["start"],
                            children={},
                        ),
                        "sync": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.sync",
                            config=ModuleConfig(
                                path="tach.sync",
                                depends_on=[
                                    "tach.check",
                                    "tach.errors",
                                    "tach.filesystem",
                                    "tach.parsing",
                                ],
                                strict=True,
                            ),
                            interface_members=[
                                "sync_project",
                                "prune_dependency_constraints",
                            ],
                            children={},
                        ),
                        "test": ModuleNode(
                            is_end_of_path=True,
                            full_path="tach.test",
                            config=ModuleConfig(
                                path="tach.test",
                                depends_on=[
                                    "tach.errors",
                                    "tach.filesystem",
                                    "tach.filesystem.git_ops",
                                    "tach.parsing",
                                ],
                                strict=False,
                            ),
                            interface_members=[],
                            children={},
                        ),
                    },
                )
            },
        )
    )


@pytest.mark.parametrize(
    "changed_files,source_root,expected_mod_paths",
    [
        (["python/tach/test.py"], "python", ["tach.test"]),
        (["tach/test.py", "tach/a/test.py"], ".", ["tach.test", "tach.a.test"]),
        (["tach/a/__init__.py"], ".", ["tach.a"]),
    ],
)
def test_get_changed_module_paths(
    tmp_path, changed_files, source_root, expected_mod_paths
):
    project_root = tmp_path
    project_config = ProjectConfig(source_root=Path(source_root))
    changed_files = [tmp_path / filepath for filepath in changed_files]
    assert set(expected_mod_paths) == set(
        get_changed_module_paths(project_root, project_config, changed_files)
    )


@pytest.mark.parametrize(
    "changed_mod_paths,expected_affected_modules",
    [
        (["tach.test"], ["tach.test", "tach.cli", "tach.__main__", "tach.start"]),
        (
            ["tach"],
            [
                "tach",
                "tach.cli",
                "tach.start",
                "tach.__main__",
                "tach.logging",
                "tach.cache",
            ],
        ),
        ([], []),
    ],
)
@patch("tach.test.get_changed_module_paths")
def test_affected_modules(
    mock_changed_module_paths,
    tmp_path,
    module_tree,
    modules,
    changed_mod_paths,
    expected_affected_modules,
):
    mock_changed_module_paths.return_value = changed_mod_paths
    project_root = tmp_path
    project_config = ProjectConfig(modules=modules)

    assert get_affected_modules(project_root, project_config, [], module_tree) == set(
        expected_affected_modules
    )
