"""Static analysis helpers that run PHP-focused tools safely."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ToolError:
    tool: str
    message: str


class AnalysisError(Exception):
    """Raised when a path cannot be sanitized or written."""


def sanitize_relative_path(relative_path: str, workspace: Path) -> Path:
    """Ensure the provided path stays within the workspace directory."""
    cleaned = relative_path.lstrip("/")
    candidate = (workspace / cleaned).resolve()
    workspace = workspace.resolve()

    if candidate == workspace:
        raise AnalysisError("Path must point to a file, not the workspace root.")

    if workspace not in candidate.parents:
        raise AnalysisError("Invalid path: outside of allowed workspace.")

    return candidate


def _run_command(command: List[str], tool: str) -> Optional[ToolError]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ToolError(tool=tool, message=f"{tool} is not available on this host.")

    output = completed.stdout.strip() or completed.stderr.strip()
    if completed.returncode == 0 and not output:
        return None

    return ToolError(tool=tool, message=output or f"{tool} reported an unknown issue.")


def _run_phpcs(command: List[str]) -> Optional[ToolError]:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return ToolError(tool="phpcs", message="phpcs is not available on this host.")

    if completed.returncode == 0:
        return None

    output = completed.stdout.strip() or completed.stderr.strip()
    if not output:
        return ToolError(tool="phpcs", message="phpcs reported an unknown issue.")

    try:
        payload = json.loads(output)
        messages: List[str] = []
        for file_report in payload.get("files", {}).values():
            for message in file_report.get("messages", []):
                line = message.get("line")
                text = message.get("message")
                messages.append(f"Line {line}: {text}")
        if messages:
            return ToolError(tool="phpcs", message="; ".join(messages))
    except json.JSONDecodeError:
        return ToolError(tool="phpcs", message=output)

    return None


def run_php_analysis(code: str, relative_path: str, workspace: Optional[Path] = None) -> dict:
    """Run PHPStan and PHPCS on the given code snippet.

    The code is written to a sanitized path inside a workspace directory to avoid
    executing tooling outside the project tree.
    """
    base_workspace = Path(workspace) if workspace else Path(__file__).resolve().parent.parent / "analysis_workspace"
    base_workspace.mkdir(parents=True, exist_ok=True)

    file_path = sanitize_relative_path(relative_path, base_workspace)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(code)

    errors: List[ToolError] = []

    phpstan_command = ["phpstan", "analyse", str(file_path), "--error-format", "raw"]
    phpstan_error = _run_command(phpstan_command, tool="phpstan")
    if phpstan_error:
        errors.append(phpstan_error)

    phpcs_command = ["phpcs", str(file_path), "--report=json"]
    phpcs_error = _run_phpcs(phpcs_command)
    if phpcs_error:
        errors.append(phpcs_error)

    return {
        "file": str(file_path),
        "errors": [error.__dict__ for error in errors],
    }
