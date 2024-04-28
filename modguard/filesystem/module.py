import os
from datetime import datetime
from typing import Optional


from modguard.constants import MODULE_FILE_NAME, CONFIG_FILE_NAME
from modguard.errors import ModguardError
from modguard.filesystem.project import find_project_config_root


def validate_module_config(root: str = ".") -> Optional[str]:
    file_path = os.path.join(root, f"{MODULE_FILE_NAME}.yml")
    if os.path.exists(file_path):
        return file_path
    file_path = os.path.join(root, f"{MODULE_FILE_NAME}.yaml")
    if os.path.exists(file_path):
        return file_path
    return


def validate_path_for_add(path: str) -> None:
    if not os.path.exists(path):
        raise ModguardError(f"{path} does not exist.")
    if os.path.isdir(path):
        if os.path.exists(
            os.path.join(path, f"{MODULE_FILE_NAME}.yml")
        ) or os.path.exists(os.path.join(path, f"{MODULE_FILE_NAME}.yaml")):
            raise ModguardError(f"{path} already contains a {MODULE_FILE_NAME}.yml")
        if not os.path.exists(os.path.join(path, "__init__.py")):
            raise ModguardError(
                f"{path} is not a valid Python package (no __init__.py found)."
            )
    # this is a file
    else:
        if not path.endswith(".py"):
            raise ModguardError(f"{path} is not a Python file.")
        if os.path.exists(path.removesuffix(".py")):
            raise ModguardError("{path} already has a directory of the same name.")
    root = find_project_config_root(path)
    if not root:
        raise ModguardError(
            f"{CONFIG_FILE_NAME} does not exist in any parent directories"
        )


def build_module(path: str, tags: Optional[set[str]]) -> str:
    dirname = path.removesuffix(".py")
    tag = os.path.basename(dirname)
    if not tags:
        tags = [tag]
    if os.path.isfile(path):
        # Create the package directory
        os.mkdir(dirname)
        # Write the __init__
        with open(f"{dirname}/__init__.py", "w") as new_init:
            new_init.write(f"""# Generated by modguard  on {datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')}
from .main import *
            """)
        # Move and rename the file
        os.rename(path, f"{dirname}/main.py")
    # Write the module.yml
    with open(f"{dirname}/{MODULE_FILE_NAME}.yml", "w") as f:
        f.write(f"tags: [{','.join(tags)}]\n")
    if not tags:
        return tag
