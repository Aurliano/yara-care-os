import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_import_linter_config_is_valid() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    search_paths = os.pathsep.join(
        [
            os.environ.get("PATH", ""),
            str(backend_root / ".venv" / "bin"),
            str(backend_root / ".venv" / "Scripts"),
        ]
    )
    lint_imports = shutil.which("lint-imports", path=search_paths)
    command = (
        [lint_imports]
        if lint_imports
        else [
            sys.executable,
            "-c",
            "from importlinter.cli import lint_imports_command; raise SystemExit(lint_imports_command() or 0)",
        ]
    )

    result = subprocess.run(
        command,
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
