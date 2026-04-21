"""
Git-based push to GitHub.
Uses local git commands instead of API - no token needed if git is already authenticated.
"""
import os
import subprocess
import config


def is_git_repo():
    """Check if project directory is a git repo"""
    git_dir = os.path.join(config.PROJECT_DIR, ".git")
    return os.path.exists(git_dir)


def get_git_status():
    """Get git status info"""
    if not is_git_repo():
        return {"is_repo": False, "has_changes": False, "branch": "", "remote": ""}

    try:
        # Check for changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=10
        )
        has_changes = bool(result.stdout.strip())

        # Get branch
        result_branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=10
        )
        branch = result_branch.stdout.strip()

        # Get remote URL
        result_remote = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=10
        )
        remote = result_remote.stdout.strip()

        return {
            "is_repo": True,
            "has_changes": has_changes,
            "branch": branch,
            "remote": remote
        }
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return {"is_repo": False, "has_changes": False, "branch": "", "remote": ""}


def git_add_commit_push(message="Update from 27TechAI Dashboard"):
    """Add, commit and push changes to GitHub"""
    if not is_git_repo():
        return False, "Not a git repository"

    try:
        # Stage website changes
        subprocess.run(
            ["git", "add", "website/"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=10,
            check=True
        )

        # Check if there are staged changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=10
        )
        # diff --cached --quiet returns 0 if no changes, 1 if there are changes
        if result.returncode == 0:
            return True, "No changes to push"

        # Commit
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=15,
            check=True
        )

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return True, "Pushed to GitHub successfully"
        else:
            error_msg = result.stderr.strip() or result.stdout.strip()
            return False, f"Push failed: {error_msg}"

    except subprocess.TimeoutExpired:
        return False, "Git operation timed out"
    except subprocess.CalledProcessError as e:
        return False, f"Git error: {e.stderr.strip() or str(e)}"
    except FileNotFoundError:
        return False, "Git is not installed or not in PATH"
    except Exception as e:
        return False, f"Error: {str(e)}"


def git_pull():
    """Pull latest changes from GitHub"""
    if not is_git_repo():
        return False, "Not a git repository"

    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=config.PROJECT_DIR,
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return True, "Pulled latest changes"
        else:
            return False, f"Pull failed: {result.stderr.strip()}"
    except Exception as e:
        return False, f"Error: {str(e)}"
