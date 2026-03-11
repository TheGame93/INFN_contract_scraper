"""Startup update check against the git remote."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from infn_jobs.config.settings import PROJECT_ROOT

_YES_VALUES = {"y", "yes"}
_SKIP_VALUES = {"1", "true", "yes"}


@dataclass(frozen=True)
class UpdateInfo:
    """Local/remote commit information for the current branch."""

    branch: str
    local_sha: str
    remote_sha: str


def _run_git(project_root: Path, *args: str, timeout_sec: float = 3.0) -> str | None:
    """Execute a git command and return stdout when successful."""
    command = ["git", "-C", str(project_root), *args]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_for_github_update(project_root: Path) -> UpdateInfo | None:
    """Return update info when the remote branch differs from local HEAD."""
    inside_worktree = _run_git(project_root, "rev-parse", "--is-inside-work-tree")
    if inside_worktree != "true":
        return None

    branch = _run_git(project_root, "rev-parse", "--abbrev-ref", "HEAD")
    if not branch or branch == "HEAD":
        return None

    local_sha = _run_git(project_root, "rev-parse", "HEAD")
    remote_line = _run_git(project_root, "ls-remote", "--heads", "origin", branch)
    if not local_sha or not remote_line:
        return None

    remote_sha = remote_line.split()[0]
    if local_sha == remote_sha:
        return None

    return UpdateInfo(branch=branch, local_sha=local_sha, remote_sha=remote_sha)


def _prompt_user(update: UpdateInfo, project_root: Path) -> bool:
    """Prompt the user when an update is available. Return True to continue."""
    print("Update available on GitHub.")
    print(f"Current: {update.local_sha[:8]}  Remote: {update.remote_sha[:8]} ({update.branch})")

    continue_now = input("Continue with the current version? [y/N]: ").strip().lower()
    if continue_now in _YES_VALUES:
        return True

    download_now = input("Download update now with 'git pull --ff-only'? [Y/n]: ").strip().lower()
    if download_now not in {"", *sorted(_YES_VALUES)}:
        print("Stopping before running the command.")
        return False

    pull_result = subprocess.run(
        ["git", "-C", str(project_root), "pull", "--ff-only"],
        check=False,
    )
    if pull_result.returncode == 0:
        print("Update downloaded. Relaunch the command to use the new version.")
        return False

    print("Update download failed. You can run 'git pull --ff-only' manually.")
    retry_continue = input("Continue with current version? [y/N]: ").strip().lower()
    return retry_continue in _YES_VALUES


def maybe_handle_startup_update_check(project_root: Path = PROJECT_ROOT) -> bool:
    """Run best-effort update check and prompt the user when needed."""
    skip_value = os.getenv("INFN_JOBS_SKIP_UPDATE_CHECK", "").strip().lower()
    if skip_value in _SKIP_VALUES:
        return True
    if not sys.stdin.isatty():
        return True

    update = check_for_github_update(project_root)
    if update is None:
        return True
    return _prompt_user(update, project_root)
