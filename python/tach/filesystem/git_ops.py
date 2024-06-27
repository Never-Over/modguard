from __future__ import annotations

from pathlib import Path

from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError, Repo

from tach.errors import TachError, TachSetupError


def get_changed_files(
    project_root: Path, head: str = "", base: str = "main"
) -> list[Path]:
    try:
        repo = Repo(project_root, search_parent_directories=True)
    except (InvalidGitRepositoryError, NoSuchPathError):
        raise TachSetupError(
            "The project does not appear to be a git repository, cannot determine changed files!"
        )

    try:
        if head:
            diff: str = repo.git.diff("--name-only", head, base)
        else:
            # If head is not provided, we can diff against 'base' from the current filesystem
            diff: str = repo.git.diff("--name-only", base)
    except GitCommandError:
        head_display = f"'{head}'" if head else "current filesystem"
        raise TachError(f"Failed to check diff between '{base}' and {head_display}!")

    changed_files = diff.splitlines()

    if not head:
        # If we are using the current filesystem, there may be relevant changes in untracked files
        untracked_files: str = repo.git.ls_files("--others", "--exclude-standard")
        changed_files.extend(untracked_files.splitlines())

    # return list of unique Paths
    return list(map(Path, set(changed_files)))


__all__ = ["get_changed_files"]