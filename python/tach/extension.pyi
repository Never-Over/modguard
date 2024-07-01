def get_project_imports(
    project_root: str,
    source_root: str,
    file_path: str,
    ignore_type_checking_imports: bool,
) -> list[tuple[str, int]]: ...
def set_excluded_paths(exclude_paths: list[str]) -> None: ...
def create_dependency_report(project_root: str, source_root: str, path: str) -> str: ...
def create_computation_cache_key(
    project_root: str,
    source_root: str,
    action: str,
    py_interpreter_version: str,
    file_dependencies: list[str],
    env_dependencies: list[str],
    backend: str,
) -> str: ...
def check_computation_cache(
    project_root: str, cache_key: str
) -> tuple[list[tuple[int, str]], int] | None: ...
def update_computation_cache(
    project_root: str, cache_key: str, value: tuple[list[tuple[int, str]], int]
) -> None: ...
