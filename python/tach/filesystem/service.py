from __future__ import annotations

import ast
import os
import stat
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Generator

from tach import errors
from tach import filesystem as fs
from tach.colors import BCOLORS
from tach.constants import ROOT_MODULE_SENTINEL_TAG
from tach.core import ModuleConfig


@dataclass
class FileInfo:
    path: str
    content: str | None = None
    canonical_path: str | None = None
    ast: ast.AST | None = None


# Thread-local file cache to avoid going to disk as much as possible
thread_local = threading.local()
# Cannot type-hint non-self attributes (https://github.com/python/mypy/issues/2388)
# cwd: str
thread_local.cwd = os.getcwd()
# file_caches_by_cwd: defaultdict[str, dict[str, FileInfo]]
thread_local.file_caches_by_cwd = defaultdict(dict)


def get_cwd() -> str:
    # Use a cached cwd to avoid system calls
    if not hasattr(thread_local, "cwd"):
        thread_local.cwd = os.getcwd()
    return thread_local.cwd


def chdir(path: str):
    # When using chdir, update the cached version
    os.chdir(path)
    thread_local.cwd = os.getcwd()


def _get_file_cache() -> dict[str, FileInfo]:
    if not hasattr(thread_local, "file_caches_by_cwd"):
        thread_local.file_caches_by_cwd = defaultdict(dict)
    file_caches_by_cwd: defaultdict[str, dict[str, FileInfo]] = (
        thread_local.file_caches_by_cwd
    )  # type: ignore
    return file_caches_by_cwd[get_cwd()]


def _file_cache_key(path: str) -> str:
    return f"{get_cwd()}:::{path}"


def _cached_file(path: str) -> FileInfo | None:
    return _get_file_cache().get(_file_cache_key(path))


def _set_cached_file(path: str, file_info: FileInfo):
    _get_file_cache()[_file_cache_key(path)] = file_info


def _remove_cached_file(path: str):
    _get_file_cache().pop(_file_cache_key(path), None)


def canonical(path: str) -> str:
    cached_file = _cached_file(path)
    if cached_file and cached_file.canonical_path:
        return cached_file.canonical_path

    result = os.path.relpath(os.path.realpath(path), start=get_cwd())

    if cached_file:
        cached_file.canonical_path = result
    else:
        _set_cached_file(path, FileInfo(path=path, canonical_path=result))

    return result


def read_file(path: str) -> str:
    cached_file = _cached_file(path)
    if cached_file and cached_file.content:
        return cached_file.content

    with open(path) as f:
        content = f.read()

    if cached_file:
        cached_file.content = content
    else:
        _set_cached_file(path, FileInfo(path=path, content=content))

    return content


def write_file(path: str, content: str):
    with open(path, "w") as f:
        f.write(content)
        print(f"{BCOLORS.WARNING}Wrote '{canonical(path)}'{BCOLORS.ENDC}")

    cached_file = _cached_file(path)
    if cached_file:
        cached_file.content = content
        cached_file.ast = None
    else:
        _set_cached_file(path, FileInfo(path=path, content=content))


def delete_file(path: str):
    _remove_cached_file(path)
    os.unlink(path)
    print(f"{BCOLORS.WARNING}Deleted '{canonical(path)}'{BCOLORS.ENDC}")


def mark_executable(path: str):
    file_path = Path(path)
    file_path.chmod(
        file_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def parse_ast(path: str) -> ast.AST:
    cached_file = _cached_file(path)
    if cached_file and cached_file.ast:
        return cached_file.ast

    if cached_file and cached_file.content:
        content = cached_file.content
        try:
            ast_result = ast.parse(cached_file.content)
        except SyntaxError as e:
            raise errors.TachParseError(f"Syntax error in {path}: {e}")
    else:
        with open(path) as f:
            content = f.read()
        try:
            ast_result = ast.parse(content)
        except SyntaxError as e:
            raise errors.TachParseError(f"Syntax error in {path}: {e}")

    if cached_file:
        cached_file.content = content
        cached_file.ast = ast_result
    else:
        _set_cached_file(path, FileInfo(path=path, content=content, ast=ast_result))

    return ast_result


def walk(
    root: Path, depth: int | None = None
) -> Generator[tuple[Path, list[Path]], None, None]:
    if depth is not None and depth <= 0:
        return
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dirpath = Path(dirpath).relative_to(root)

        if rel_dirpath.name.startswith("."):
            # This prevents recursing into child directories of hidden paths
            del dirnames[:]
            continue

        if depth:
            # Ignore anything past requested depth
            current_depth = len(rel_dirpath.parts) - 1
            if current_depth > depth:
                continue

        def filter_filename(filename: str) -> bool:
            return not filename.startswith(".")

        yield rel_dirpath, list(map(Path, filter(filter_filename, filenames)))


def walk_pyfiles(root: Path, depth: int | None = None) -> Generator[Path, None, None]:
    for dirpath, filepaths in walk(root, depth=depth):
        for filepath in filepaths:
            if filepath.name.endswith(".py"):
                yield dirpath / filepath


@lru_cache(maxsize=None)
def file_to_module_path(source_root: Path, file_path: Path) -> str:
    # Assuming that the file_path has been 'canonicalized' and does not traverse multiple directories
    file_path = file_path.relative_to(source_root)
    if file_path == Path("."):
        return ""

    module_path = str(file_path).replace(os.sep, ".")

    if module_path.endswith(".py"):
        module_path = module_path[:-3]
    if module_path.endswith(".__init__"):
        module_path = module_path[:-9]
    if module_path == "__init__":
        return ""

    return module_path


@lru_cache(maxsize=None)
def module_to_file_path_no_members(source_root: Path, module_path: str) -> Path | None:
    """
    This resolves a dotted Python module path ('a.b.c')
    into a Python file path or a Python package __init__.py
    """
    if module_path == ROOT_MODULE_SENTINEL_TAG:
        root_path = Path("__init__.py")
        if root_path.exists():
            return root_path
        return None

    base_path = module_path.replace(".", os.sep)
    pyfile_path = source_root / f"{base_path}.py"
    init_py_path = source_root / base_path / "__init__.py"
    if pyfile_path.exists():
        return pyfile_path
    elif init_py_path.exists():
        return init_py_path

    return None


@lru_cache(maxsize=None)
def module_to_pyfile_or_dir_path(source_root: Path, module_path: str) -> Path | None:
    """
    This resolves a dotted Python module path ('a.b.c')
    into a Python file or a Python package directory
    """
    if not module_path:
        # Path("") turns into PosixPath("."), but we don't want to
        # treat an empty module path as the root directory
        return None

    base_path = module_path.replace(".", os.sep)
    pyfile_path = source_root / f"{base_path}.py"
    dir_path = source_root / base_path
    if pyfile_path.exists():
        return pyfile_path
    elif dir_path.is_dir():
        return dir_path

    return None


@dataclass
class ProjectModuleValidationResult:
    valid_modules: list[ModuleConfig] = field(default_factory=list)
    invalid_modules: list[ModuleConfig] = field(default_factory=list)


def validate_project_modules(
    source_root: Path,
    modules: list[ModuleConfig],
) -> ProjectModuleValidationResult:
    result = ProjectModuleValidationResult()
    for module in modules:
        if module.path == ROOT_MODULE_SENTINEL_TAG or fs.module_to_pyfile_or_dir_path(
            source_root=source_root, module_path=module.path
        ):
            result.valid_modules.append(module)
        else:
            result.invalid_modules.append(module)
    return result
