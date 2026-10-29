import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env if present
load_dotenv()

DEFAULT_GRAPH_VERSION = "v22.0"
DEFAULT_DELAY_SECONDS = 2.5
DEFAULT_DELAY_JITTER = 0.4
MIN_SCHEDULE_MINUTES = 15       # Meta minimum is 10 min; 15 min adds a 5 min safety buffer
MAX_SCHEDULE_DAYS = 29          # Meta maximum is 30 days; 29 days + 23h keeps it safely within bounds
DEFAULT_POSTS_PER_DAY = 3
DEFAULT_SLOTS = ["09:00", "14:00", "20:00"]


@dataclass
class Config:
    page_id: str
    access_token: str
    api_version: str = DEFAULT_GRAPH_VERSION
    delay_seconds: float = DEFAULT_DELAY_SECONDS
    delay_jitter: float = DEFAULT_DELAY_JITTER
    state_file: Path = Path(".lazymeta_state.json")

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "Config":
        if env_path and env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            load_dotenv(override=True)

        page_id = os.getenv("META_PAGE_ID", "").strip()
        access_token = os.getenv("META_PAGE_ACCESS_TOKEN", "").strip()
        api_version = os.getenv("META_GRAPH_VERSION", DEFAULT_GRAPH_VERSION).strip()

        try:
            delay = float(os.getenv("META_REQUEST_DELAY", DEFAULT_DELAY_SECONDS))
        except ValueError:
            delay = DEFAULT_DELAY_SECONDS

        return cls(
            page_id=page_id,
            access_token=access_token,
            api_version=api_version,
            delay_seconds=delay,
        )


def check_git_security(repo_root: Path = Path(".")) -> list[str]:
    """Inspects the git repository to ensure secrets like .env are never tracked."""
    warnings: list[str] = []
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return warnings

    try:
        # Check if .env is tracked in git index
        res = subprocess.run(
            ["git", "ls-files", ".env"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.stdout.strip():
            warnings.append(
                "CRITICAL SECURITY ALERT: '.env' is currently tracked by git! "
                "Run 'git rm --cached .env' immediately to avoid exposing secrets on public remotes."
            )

        # Check if .gitignore exists and contains .env
        gitignore = repo_root / ".gitignore"
        if not gitignore.exists():
            warnings.append("'.gitignore' file is missing. Sensitive files may be accidentally committed.")
        else:
            content = gitignore.read_text(encoding="utf-8")
            if ".env" not in content:
                warnings.append("'.gitignore' does not contain '.env'. Add '.env' to prevent credential leaks.")
    except Exception:
        pass

    return warnings
