from __future__ import annotations

import os
from pathlib import Path

import pytest
from git import Repo

from tach.filesystem.git_ops import get_changed_files


@pytest.fixture
def git_repo(tmp_path):
    os.environ["GIT_AUTHOR_NAME"] = "Temporary User"
    os.environ["GIT_AUTHOR_EMAIL"] = "temporary.user@example.com"
    os.environ["GIT_COMMITTER_NAME"] = "Temporary User"
    os.environ["GIT_COMMITTER_EMAIL"] = "temporary.user@example.com"

    repo_path = tmp_path / "test_repo"
    repo = Repo.init(repo_path, initial_branch="main")

    files = {
        "file1.txt": "Hello, World!",
        "dir1/file2.txt": "This is file 2.",
        "dir2/file3.txt": "This is file 3.",
    }

    for file_path, content in files.items():
        full_path = repo_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

    repo.git.add("-A")
    repo.git.commit("-m", "Initial commit on main branch")

    yield repo_path

    del os.environ["GIT_AUTHOR_NAME"]
    del os.environ["GIT_AUTHOR_EMAIL"]
    del os.environ["GIT_COMMITTER_NAME"]
    del os.environ["GIT_COMMITTER_EMAIL"]


@pytest.mark.parametrize(
    "setup_changes, expected_files",
    [
        (lambda repo_path: None, set()),
        (
            lambda repo_path: {
                (repo_path / "dir1/file4.txt").write_text("This is file 4."),
                (repo_path / "dir2/file5.txt").write_text("This is file 5."),
            },
            {"dir1/file4.txt", "dir2/file5.txt"},
        ),
        (
            lambda repo_path: {
                (repo_path / "file1.txt").unlink(),
                (repo_path / "dir1/file2.txt").unlink(),
            },
            {"file1.txt", "dir1/file2.txt"},
        ),
        (
            lambda repo_path: {
                (repo_path / "file1.txt").rename(repo_path / "file1_renamed.txt"),
                (repo_path / "dir1/file2.txt").rename(
                    repo_path / "dir1/file2_renamed.txt"
                ),
            },
            {
                "file1.txt",
                "file1_renamed.txt",
                "dir1/file2.txt",
                "dir1/file2_renamed.txt",
            },
        ),
    ],
)
def test_changed_files_new_branch(git_repo, setup_changes, expected_files):
    repo_path = git_repo
    repo = Repo(repo_path)

    repo.git.checkout("-b", "new_branch")

    if setup_changes:
        setup_changes(repo_path)

    repo.git.add("-A")
    repo.git.commit("-m", "Changes on new_branch", "--allow-empty")

    changed_files = get_changed_files(repo_path, base="main", head="new_branch")

    assert set(changed_files) == set(Path(filepath) for filepath in expected_files)


@pytest.mark.parametrize(
    "setup_changes, expected_files",
    [
        (lambda repo_path: None, set()),
        (
            lambda repo_path: {
                (repo_path / "dir1/file4.txt").write_text("This is file 4."),
                (repo_path / "dir2/file5.txt").write_text("This is file 5."),
            },
            {"dir1/file4.txt", "dir2/file5.txt"},
        ),
        (
            lambda repo_path: {
                (repo_path / "file1.txt").unlink(),
                (repo_path / "dir1/file2.txt").unlink(),
            },
            {"file1.txt", "dir1/file2.txt"},
        ),
        (
            lambda repo_path: {
                (repo_path / "file1.txt").rename(repo_path / "file1_renamed.txt"),
                (repo_path / "dir1/file2.txt").rename(
                    repo_path / "dir1/file2_renamed.txt"
                ),
            },
            {
                "file1.txt",
                "file1_renamed.txt",
                "dir1/file2.txt",
                "dir1/file2_renamed.txt",
            },
        ),
    ],
)
def test_changed_files_working_directory(git_repo, setup_changes, expected_files):
    if setup_changes:
        setup_changes(git_repo)

    changed_files = get_changed_files(git_repo, base="main")

    assert set(changed_files) == set(Path(filepath) for filepath in expected_files)
