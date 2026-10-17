import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
VENV_SCRIPTS = PROJECT_DIR / ".venv" / "Scripts"


def find_langgraph() -> Path:
    candidates = [
        VENV_SCRIPTS / "langgraph.exe",
        Path(sys.executable).resolve().parent / "langgraph.exe",
    ]
    for langgraph in candidates:
        if langgraph.exists():
            return langgraph

    raise FileNotFoundError(
        "Khong tim thay langgraph.exe. Hay tao .venv Python 3.11+ va chay: "
        ".venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    )


def main() -> int:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

    langgraph = find_langgraph()
    return subprocess.call([str(langgraph), "dev", "--no-browser"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Loi khi khoi dong LangGraph: {exc}", file=sys.stderr)
        raise SystemExit(1)
