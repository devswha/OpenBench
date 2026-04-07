from __future__ import annotations

from pathlib import Path
import re


def extract_task_id(prompt: str) -> str | None:
    match = re.search(r"Task ID:\s*([A-Za-z0-9_-]+)", prompt)
    return match.group(1) if match else None


def apply_task(task_id: str, workspace: Path) -> None:
    if task_id == "single-file-bug-fix":
        _replace_once(workspace / "calculator.py", "return a - b", "return a + b")
    elif task_id == "failing-unit-test-repair":
        _replace_once(
            workspace / "text_utils.py",
            'return value.strip().lower().replace(" ", "_")',
            'return value.strip().lower().replace(" ", "-")',
        )
    elif task_id == "config-schema-migration":
        (workspace / "config_loader.py").write_text(
            "def load_timeout(config: dict) -> int:\n"
            "    if \"timeout_seconds\" in config:\n"
            "        return int(config[\"timeout_seconds\"])\n"
            "    return config[\"timeout_ms\"] // 1000\n"
        )
    elif task_id == "multi-file-import-repair":
        _replace_once(
            workspace / "app.py",
            "from helpers.math_ops import safe_add",
            "from utils.math_ops import safe_add",
        )
        _replace_once(
            workspace / "report.py",
            "from helpers.math_ops import safe_add",
            "from utils.math_ops import safe_add",
        )
    elif task_id == "validation-error-handling-patch":
        (workspace / "user_service.py").write_text(
            "def create_user(email: str, name: str) -> dict:\n"
            "    cleaned_email = email.strip()\n"
            "    if not cleaned_email:\n"
            "        raise ValueError(\"email must not be blank\")\n"
            "    return {\"email\": cleaned_email, \"name\": name.strip()}\n"
        )
    else:
        raise SystemExit(f"unknown task id: {task_id}")


def _replace_once(path: Path, old: str, new: str) -> None:
    content = path.read_text()
    if old not in content:
        raise SystemExit(f"expected text not found in {path}: {old!r}")
    path.write_text(content.replace(old, new, 1))
