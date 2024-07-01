from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import IO, TYPE_CHECKING, Any

from tach import __version__, cache
from tach import filesystem as fs
from tach.check import BoundaryError, check
from tach.colors import BCOLORS
from tach.constants import CONFIG_FILE_NAME, TOOL_NAME
from tach.core import ProjectConfig
from tach.errors import TachError
from tach.extension import (
    check_computation_cache,
    create_computation_cache_key,
    update_computation_cache,
)
from tach.filesystem import install_pre_commit
from tach.logging import LogDataModel, logger
from tach.mod import mod_edit_interactive
from tach.parsing import parse_project_config
from tach.report import report
from tach.show import generate_show_url
from tach.sync import prune_dependency_constraints, sync_project
from tach.test import run_affected_tests

if TYPE_CHECKING:
    from tach.core import UnusedDependencies


class TerminalEnvironment(Enum):
    UNKNOWN = 1
    JETBRAINS = 2
    VSCODE = 3


@lru_cache
def detect_environment() -> TerminalEnvironment:
    if "jetbrains" in os.environ.get("TERMINAL_EMULATOR", "").lower():
        return TerminalEnvironment.JETBRAINS
    elif "vscode" in os.environ.get("TERM_PROGRAM", "").lower():
        return TerminalEnvironment.VSCODE
    return TerminalEnvironment.UNKNOWN


def create_clickable_link(
    file_path: Path, display_path: Path | None = None, line: int | None = None
) -> str:
    terminal_env = detect_environment()
    abs_path = file_path.resolve()

    if terminal_env == TerminalEnvironment.JETBRAINS:
        link = f"file://{abs_path}:{line}" if line is not None else f"file://{abs_path}"
    elif terminal_env == TerminalEnvironment.VSCODE:
        link = (
            f"vscode://file/{abs_path}:{line}"
            if line is not None
            else f"vscode://file/{abs_path}"
        )
    else:
        # For generic terminals, use a standard file link
        link = f"file://{abs_path}"

    # ANSI escape codes for clickable link
    if line:
        # Show the line number if we have it
        display_file_path = f"{display_path or file_path}[L{line}]"
    else:
        display_file_path = str(display_path) if display_path else str(file_path)
    clickable_link = f"\033]8;;{link}\033\\{display_file_path}\033]8;;\033\\"
    return clickable_link


def build_error_message(error: BoundaryError, source_root: Path) -> str:
    error_location = create_clickable_link(
        source_root / error.file_path,
        display_path=error.file_path,
        line=error.line_number,
    )
    error_template = f"❌ {BCOLORS.FAIL}{error_location}{BCOLORS.ENDC}{BCOLORS.WARNING}: {{message}} {BCOLORS.ENDC}"
    error_info = error.error_info
    if error_info.exception_message:
        return error_template.format(message=error_info.exception_message)
    elif not error_info.is_dependency_error:
        return error_template.format(message="Unexpected error")

    message = (
        f"Cannot import '{error.import_mod_path}'. "
        f"Tag '{error_info.source_module}' cannot depend on '{error_info.invalid_module}'."
    )

    return error_template.format(message=message)


def print_warnings(warning_list: list[str]) -> None:
    for warning in warning_list:
        print(f"{BCOLORS.WARNING}{warning}{BCOLORS.ENDC}", file=sys.stderr)


def print_errors(error_list: list[BoundaryError], source_root: Path) -> None:
    if not error_list:
        return
    sorted_results = sorted(error_list, key=lambda e: e.file_path)
    for error in sorted_results:
        print(
            build_error_message(error, source_root=source_root),
            file=sys.stderr,
        )
    print(
        f"{BCOLORS.WARNING}\nIf you intended to add a new dependency, run 'tach sync' to update your module configuration."
        f"\nOtherwise, remove any disallowed imports and consider refactoring.\n{BCOLORS.ENDC}"
    )


def print_unused_dependencies(
    all_unused_dependencies: list[UnusedDependencies],
) -> None:
    constraint_messages = "\n".join(
        f"\t{BCOLORS.WARNING}'{unused_dependencies.path}' does not depend on: {unused_dependencies.dependencies}{BCOLORS.ENDC}"
        for unused_dependencies in all_unused_dependencies
    )
    print(
        f"❌ {BCOLORS.FAIL}Found unused dependencies: {BCOLORS.ENDC}\n"
        + constraint_messages
    )
    print(
        f"{BCOLORS.WARNING}\nRemove the unused dependencies from tach.yml, "
        f"or consider running 'tach sync --prune' to update module configuration and "
        f"eliminate all unused dependencies.\n{BCOLORS.ENDC}"
    )


def print_no_config_yml() -> None:
    print(
        f"{BCOLORS.FAIL} {CONFIG_FILE_NAME}.(yml|yaml) not found{BCOLORS.ENDC}",
        file=sys.stderr,
    )


def add_base_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-e",
        "--exclude",
        required=False,
        type=str,
        metavar="file_or_path,...",
        help="Comma separated path list to exclude. tests/, ci/, etc.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tach",
        add_help=True,
        epilog="Make sure tach is run from the root of your Python project,"
        " and `tach.yml` is present",
    )
    parser.add_argument("--version", action="version", version=f"tach {__version__}")

    subparsers = parser.add_subparsers(title="commands", dest="command")
    mod_parser = subparsers.add_parser(
        "mod",
        prog="tach mod",
        help="Configure module boundaries interactively",
        description="Configure module boundaries interactively",
    )
    mod_parser.add_argument(
        "-d",
        "--depth",
        type=int,
        nargs="?",
        default=None,
        help="The number of child directories to expand from the root",
    )
    add_base_arguments(mod_parser)
    check_parser = subparsers.add_parser(
        "check",
        prog="tach check",
        help="Check existing boundaries against your dependencies and module interfaces",
        description="Check existing boundaries against your dependencies and module interfaces",
    )
    check_parser.add_argument(
        "--exact",
        action="store_true",
        help="Raise errors if any dependency constraints are unused.",
    )
    add_base_arguments(check_parser)
    sync_parser = subparsers.add_parser(
        "sync",
        prog="tach sync",
        help="Sync constraints with actual dependencies in your project.",
        description="Sync constraints with actual dependencies in your project.",
    )
    sync_parser.add_argument(
        "--prune",
        action="store_true",
        help="Prune all existing constraints and re-sync dependencies.",
    )
    add_base_arguments(sync_parser)
    report_parser = subparsers.add_parser(
        "report",
        prog="tach report",
        help="Create a report of dependencies and usages of the given path or directory.",
        description="Create a report of dependencies and usages of the given path or directory.",
    )
    report_parser.add_argument(
        "path", help="The path or directory path used to generate the report."
    )
    subparsers.add_parser(
        "show",
        prog="tach show",
        help="Visualize the dependency graph of your project on the web.",
        description="Visualize the dependency graph of your project on the web.",
    )
    install_parser = subparsers.add_parser(
        "install",
        prog="tach install",
        help="Install tach into your workflow (e.g. as a pre-commit hook)",
        description="Install tach into your workflow (e.g. as a pre-commit hook)",
    )
    install_parser.add_argument(
        "target",
        choices=InstallTarget.choices(),
        help="What kind of installation to perform (e.g. pre-commit)",
    )
    add_base_arguments(report_parser)
    test_parser = subparsers.add_parser(
        "test",
        prog="tach test",
        help="Run tests on modules impacted by the current changes.",
        description="Run tests on modules impacted by the current changes.",
    )
    test_parser.add_argument(
        "--base",
        type=str,
        nargs="?",
        default="main",
        help="The base commit to use when determining which modules are impacted by changes. [default: 'main']",
    )

    test_parser.add_argument(
        "--head",
        type=str,
        nargs="?",
        default="",
        help="The head commit to use when determining which modules are impacted by changes. [default: current filesystem]",
    )
    test_parser.add_argument(
        "--disable-cache",
        action="store_true",
        help="Do not check cache for results, and do not push results to cache.",
    )
    test_parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to pytest. Use '--' to separate these arguments. Ex: 'tach test -- -v'",
    )
    return parser


def parse_arguments(
    args: list[str],
) -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = build_parser()
    parsed_args = parser.parse_args(args)
    return parsed_args, parser


@dataclass
class CachedOutput:
    key: str
    output: list[tuple[int, str]] = field(default_factory=list)
    exit_code: int | None = None

    @property
    def exists(self) -> bool:
        return self.exit_code is not None

    def replay(self):
        for fd, output in self.output:
            if fd == 1:
                print(output, end="", file=sys.stdout)
            elif fd == 2:
                print(output, end="", file=sys.stderr)


def check_cache_for_action(
    project_root: Path, project_config: ProjectConfig, action: str
) -> CachedOutput:
    cache_key = create_computation_cache_key(
        project_root=str(project_root),
        source_root=str(project_config.source_root),
        action=action,
        py_interpreter_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        file_dependencies=project_config.cache.file_dependencies,
        env_dependencies=project_config.cache.env_dependencies,
        backend=project_config.cache.backend,
    )
    cache_result = check_computation_cache(
        project_root=str(project_root), cache_key=cache_key
    )
    if cache_result:
        return CachedOutput(
            key=cache_key,
            output=cache_result[0],
            exit_code=cache_result[1],
        )
    return CachedOutput(key=cache_key)


class TeeStream:
    def __init__(self, fd: int, source_stream: IO[Any], capture: list[tuple[int, str]]):
        self.fd = fd
        self.source_stream = source_stream
        self.capture = capture

    def write(self, data: Any):
        self.source_stream.write(data)
        self.capture.append((self.fd, data))

    def __getattr__(self, name: str) -> Any:
        # Hack: Proxy attribute access to the source stream
        return getattr(self.source_stream, name)


class Tee:
    def __init__(self):
        # stdout output will be indicated by (1, <data>), stderr output by (2, <data>)
        self.output_capture: list[tuple[int, str]] = []
        self.original_stdout: Any = None
        self.original_stderr: Any = None

    def __enter__(self):
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

        sys.stdout = TeeStream(1, sys.stdout, self.output_capture)
        sys.stderr = TeeStream(2, sys.stderr, self.output_capture)

        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


def tach_check(
    project_root: Path,
    exact: bool = False,
    exclude_paths: list[str] | None = None,
):
    logger.info(
        "tach check called",
        extra={
            "data": LogDataModel(
                function="tach_check",
                parameters={"exact": exact},
            ),
        },
    )
    try:
        project_config = parse_project_config(project_root)
        if project_config is None:
            print_no_config_yml()
            sys.exit(1)

        exact |= project_config.exact

        check_result = check(
            project_root=project_root,
            project_config=project_config,
            exclude_paths=exclude_paths,
        )
        if check_result.warnings:
            print_warnings(check_result.warnings)

        exit_code = 0

        if check_result.errors:
            print_errors(
                check_result.errors,
                source_root=project_root / project_config.source_root,
            )
            exit_code = 1

        # If we're checking in strict mode, we want to verify that pruning constraints has no effect
        if exact:
            pruned_config = prune_dependency_constraints(
                project_root=project_root,
                project_config=project_config,
                exclude_paths=exclude_paths,
            )
            unused_dependencies = pruned_config.compare_dependencies(project_config)
            if unused_dependencies:
                print_unused_dependencies(unused_dependencies)
                exit_code = 1
    except Exception as e:
        print(str(e))
        sys.exit(1)

    if exit_code == 0:
        print(f"✅ {BCOLORS.OKGREEN}All module dependencies validated!{BCOLORS.ENDC}")
    sys.exit(exit_code)


def tach_mod(
    project_root: Path, depth: int | None = 1, exclude_paths: list[str] | None = None
):
    logger.info(
        "tach mod called",
        extra={
            "data": LogDataModel(
                function="tach_mod",
                parameters={"depth": depth},
            ),
        },
    )
    try:
        project_config = parse_project_config(root=project_root) or ProjectConfig()
        saved_changes, warnings = mod_edit_interactive(
            project_root=project_root, project_config=project_config, depth=depth
        )
    except Exception as e:
        print(str(e))
        sys.exit(1)

    if warnings:
        print("\n".join(warnings))
    if saved_changes:
        print(
            f"✅ {BCOLORS.OKGREEN}Set modules! You may want to run '{TOOL_NAME} sync' "
            f"to automatically set boundaries.{BCOLORS.ENDC}"
        )
    sys.exit(0)


def tach_sync(
    project_root: Path, prune: bool = False, exclude_paths: list[str] | None = None
):
    logger.info(
        "tach sync called",
        extra={
            "data": LogDataModel(
                function="tach_sync",
                parameters={"prune": prune},
            ),
        },
    )
    try:
        project_config = parse_project_config(root=project_root)
        if project_config is None:
            print_no_config_yml()
            sys.exit(1)

        if exclude_paths is not None and project_config.exclude is not None:
            exclude_paths.extend(project_config.exclude)
        else:
            exclude_paths = project_config.exclude

        sync_project(
            project_root=project_root,
            project_config=project_config,
            prune=prune,
            exclude_paths=exclude_paths,
        )
    except Exception as e:
        print(str(e))
        sys.exit(1)

    print(f"✅ {BCOLORS.OKGREEN}Synced dependencies.{BCOLORS.ENDC}")
    sys.exit(0)


class InstallTarget(Enum):
    PRE_COMMIT = "pre-commit"

    @classmethod
    def choices(cls) -> list[str]:
        return [item.value for item in cls]


def tach_install(project_root: Path, target: InstallTarget) -> None:
    logger.info(
        "tach install called",
        extra={
            "data": LogDataModel(
                function="tach_install",
            ),
        },
    )
    try:
        if target == InstallTarget.PRE_COMMIT:
            installed, warning = install_pre_commit(project_root=project_root)
        else:
            raise NotImplementedError(f"Target {target} is not supported by 'install'.")
    except Exception as e:
        print(str(e))
        sys.exit(1)

    if installed:
        print(
            f"✅ {BCOLORS.OKGREEN}Pre-commit hook installed to '.git/hooks/pre-commit'.{BCOLORS.ENDC}"
        )
        sys.exit(0)
    else:
        print(
            f"{BCOLORS.WARNING}Pre-commit hook could not be installed: {warning} {BCOLORS.ENDC}"
        )
        sys.exit(1)


def tach_report(project_root: Path, path: str, exclude_paths: list[str] | None = None):
    logger.info(
        "tach report called",
        extra={
            "data": LogDataModel(
                function="tach_report",
            ),
        },
    )
    project_config = parse_project_config(root=project_root)
    if project_config is None:
        print_no_config_yml()
        sys.exit(1)

    report_path = Path(path)
    try:
        print(
            report(
                project_root,
                report_path,
                project_config=project_config,
                exclude_paths=exclude_paths,
            )
        )
        sys.exit(0)
    except TachError as e:
        print(f"Report failed: {e}")
        sys.exit(1)


def tach_show(project_root: Path):
    logger.info(
        "tach show called",
        extra={
            "data": LogDataModel(
                function="tach_show",
            ),
        },
    )

    project_config = parse_project_config(root=project_root)
    if project_config is None:
        print_no_config_yml()
        sys.exit(1)

    try:
        result = generate_show_url(project_config)
        if result:
            print("View your dependency graph here:")
            print(result)
            sys.exit(0)
        else:
            sys.exit(1)
    except TachError as e:
        print(f"Show failed: {e}")
        sys.exit(1)


def tach_test(
    project_root: Path,
    head: str,
    base: str,
    disable_cache: bool,
    pytest_args: list[Any],
):
    logger.info(
        "tach test called",
        extra={
            "data": LogDataModel(
                function="tach_test",
            ),
        },
    )
    project_config = parse_project_config(root=project_root)
    if project_config is None:
        print_no_config_yml()
        sys.exit(1)

    if pytest_args and pytest_args[0] != "--":
        print(
            f"{BCOLORS.FAIL}Unknown arguments received. Use '--' to separate arguments for pytest. Ex: 'tach test -- -v'{BCOLORS.ENDC}"
        )
        sys.exit(1)

    try:
        if disable_cache:
            # If cache disabled, just run affected tests and exit
            exit_code = run_affected_tests(
                project_root=project_root,
                project_config=project_config,
                head=head,
                base=base,
                pytest_args=pytest_args[1:],  # Remove '--' pseudo-argument
            )
            sys.exit(exit_code)

        cached_output = check_cache_for_action(
            project_root, project_config, f"tach-test,{head},{base},{pytest_args}"
        )
        if cached_output.exists:
            # Early exit, cached terminal output was found
            print(
                f"{BCOLORS.OKGREEN}============ Cached results found!  ============{BCOLORS.ENDC}"
            )
            cached_output.replay()
            print(
                f"{BCOLORS.OKGREEN}============ END Cached results  ============{BCOLORS.ENDC}"
            )
            sys.exit(cached_output.exit_code)

        # Cache missed, capture terminal output while tests run so we can update the cache

        with Tee() as captured:
            exit_code = run_affected_tests(
                project_root=project_root,
                project_config=project_config,
                head=head,
                base=base,
                pytest_args=pytest_args[1:],  # Remove '--' pseudo-argument
            )

        update_computation_cache(
            str(project_root),
            cache_key=cached_output.key,
            value=(captured.output_capture, exit_code),
        )
        sys.exit(exit_code)
    except TachError as e:
        print(f"{BCOLORS.FAIL}Report failed: {e}{BCOLORS.ENDC}")
        sys.exit(1)


def main() -> None:
    args, parser = parse_arguments(sys.argv[1:])
    project_root = fs.find_project_config_root() or Path.cwd()

    latest_version = cache.get_latest_version()
    if latest_version and latest_version != __version__:
        print(
            f"{BCOLORS.WARNING}WARNING: there is a new tach version available"
            f" ({__version__} -> {latest_version}). Upgrade to remove this warning.{BCOLORS.ENDC}"
        )

    # TODO: rename throughout to 'exclude_patterns' to indicate that these are regex patterns
    exclude_paths = args.exclude.split(",") if getattr(args, "exclude", None) else None

    if args.command == "mod":
        tach_mod(
            project_root=project_root, depth=args.depth, exclude_paths=exclude_paths
        )
    elif args.command == "sync":
        tach_sync(
            project_root=project_root, prune=args.prune, exclude_paths=exclude_paths
        )
    elif args.command == "check":
        tach_check(
            project_root=project_root, exact=args.exact, exclude_paths=exclude_paths
        )
    elif args.command == "install":
        try:
            install_target = InstallTarget(args.target)
        except ValueError:
            print(f"{args.target} is not a valid installation target.")
            sys.exit(1)
        tach_install(project_root=project_root, target=install_target)
    elif args.command == "report":
        tach_report(
            project_root=project_root, path=args.path, exclude_paths=exclude_paths
        )
    elif args.command == "test":
        tach_test(
            project_root=project_root,
            head=args.head,
            base=args.base,
            disable_cache=args.disable_cache,
            pytest_args=args.pytest_args,
        )
    elif args.command == "show":
        tach_show(project_root=project_root)
    else:
        print("Unrecognized command")
        parser.print_help()
        exit(1)


__all__ = ["main"]
