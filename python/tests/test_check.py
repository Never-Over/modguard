from __future__ import annotations

from itertools import chain
from pathlib import Path
from unittest.mock import patch

import pytest

from tach.check import check_import
from tach.cli import tach_check
from tach.core import (
    ModuleConfig,
    ModuleNode,
    ModuleTree,
)
from tach.core.config import RootModuleConfig
from tach.filesystem import validate_project_modules


@pytest.fixture
def example_dir() -> Path:
    current_dir = Path(__file__).parent
    return current_dir / "example"


@pytest.fixture
def test_config() -> ModuleConfig:
    return ModuleConfig(path="test", strict=False)


@pytest.fixture
def module_tree() -> ModuleTree:
    return ModuleTree(
        root=ModuleNode(
            is_end_of_path=False,
            full_path="",
            config=None,
            children={
                "domain_one": ModuleNode(
                    is_end_of_path=True,
                    full_path="domain_one",
                    config=ModuleConfig(
                        path="domain_one",
                        depends_on=["domain_one.subdomain", "domain_three"],
                        strict=True,
                    ),
                    interface_members=["public_fn"],
                    children={
                        "subdomain": ModuleNode(
                            is_end_of_path=True,
                            full_path="domain_one.subdomain",
                            config=ModuleConfig(
                                path="domain_one.subdomain", strict=True
                            ),
                            children={},
                        )
                    },
                ),
                "domain_two": ModuleNode(
                    is_end_of_path=True,
                    full_path="domain_two",
                    config=ModuleConfig(
                        path="domain_two", depends_on=["domain_one"], strict=False
                    ),
                    children={
                        "subdomain": ModuleNode(
                            is_end_of_path=True,
                            full_path="domain_two.subdomain",
                            config=ModuleConfig(
                                path="domain_two",
                                depends_on=["domain_one"],
                                strict=False,
                            ),
                            children={},
                        )
                    },
                ),
                "domain_three": ModuleNode(
                    is_end_of_path=True,
                    full_path="domain_three",
                    config=ModuleConfig(path="domain_three", strict=False),
                    children={},
                ),
            },
        )
    )


@pytest.mark.parametrize(
    "valid_modules,invalid_modules",
    [
        (["mod.a"], []),
        ([], ["mod.b"]),
        (["mod.a", "mod.b"], ["mod.c"]),
        (["mod.a", "mod.b"], ["mod.c", "mod.d"]),
    ],
)
def test_validate_project_modules(tmp_path, valid_modules, invalid_modules):
    def mock_fs_check(source_root, module_path):
        return module_path in valid_modules

    mock_source_root = tmp_path / "src"
    with patch("tach.filesystem.module_to_pyfile_or_dir_path", wraps=mock_fs_check):
        result = validate_project_modules(
            mock_source_root,
            [ModuleConfig(path=path) for path in chain(valid_modules, invalid_modules)],
        )
        assert set(mod.path for mod in result.valid_modules) == set(valid_modules)
        assert set(mod.path for mod in result.invalid_modules) == set(invalid_modules)


@patch("tach.filesystem.module_to_pyfile_or_dir_path")
def test_validate_project_modules_root_is_always_valid(tmp_path):
    result = validate_project_modules(tmp_path / "src", [RootModuleConfig()])
    assert (
        len(result.valid_modules) == 1 and result.valid_modules[0] == RootModuleConfig()
    )
    assert not result.invalid_modules


@pytest.mark.parametrize(
    "file_mod_path,import_mod_path,expected_result",
    [
        ("domain_one", "domain_one", True),
        ("domain_one", "domain_one.subdomain", True),
        ("domain_one", "domain_one.core", True),
        ("domain_one", "domain_three", True),
        ("domain_two", "domain_one", True),
        ("domain_two", "domain_one.public_fn", True),
        ("domain_two.subdomain", "domain_one", True),
        ("domain_two", "external", True),
        ("external", "external", True),
        ("domain_two", "domain_one.private_fn", False),
        ("domain_three", "domain_one", False),
        ("domain_two", "domain_one.core", False),
        ("domain_two.subdomain", "domain_one.core", False),
        ("domain_two", "domain_three", False),
        ("domain_two", "domain_two.subdomain", False),
        ("external", "domain_three", False),
    ],
)
def test_check_import(module_tree, file_mod_path, import_mod_path, expected_result):
    check_error = check_import(
        module_tree=module_tree,
        file_mod_path=file_mod_path,
        import_mod_path=import_mod_path,
    )
    result = check_error is None
    assert result == expected_result


def test_valid_example_dir(example_dir):
    project_root = example_dir / "valid"
    with pytest.raises(SystemExit) as exc_info:
        tach_check(project_root=project_root)
    assert exc_info.value.code == 0


def test_valid_example_dir_monorepo(example_dir):
    project_root = example_dir / "monorepo"
    with pytest.raises(SystemExit) as exc_info:
        tach_check(project_root=project_root)
    assert exc_info.value.code == 0
