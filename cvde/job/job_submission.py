import subprocess
from dataclasses import dataclass
from typing import Any
import cvde


@dataclass
class JobSubmission:
    job_name: str
    run_name: str
    config: dict[str, Any]
    tags: list[str]
    env: dict[str, str]
    diff: str | None = None
    commit: str | None = None

    def __post_init__(self) -> None:
        if not cvde.Workspace().git_tracking_enabled:
            return

        subprocess.run(["git", "add", "-A"], capture_output=True)
        self.diff = subprocess.run(["git", "diff", "HEAD"], capture_output=True).stdout.decode()
        subprocess.run(["git", "reset", "HEAD"])

        self.commit = (
            subprocess.run("git rev-parse HEAD".split(), capture_output=True)
            .stdout.decode()
            .strip()
        )

    def __hash__(self) -> int:
        return hash(self.run_name)
