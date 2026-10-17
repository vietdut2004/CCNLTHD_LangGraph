import os
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHON = PROJECT_DIR / ".venv" / "Scripts" / "python.exe"


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    python = str(VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable))
    return subprocess.call([python, "-m", "uvicorn", "main:app", "--reload"])


if __name__ == "__main__":
    raise SystemExit(main())
