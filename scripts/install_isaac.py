"""Install Isaac Sim with uv, which handles long Windows installation paths."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
expected = root / ".venv"
if Path(sys.prefix).resolve() != expected.resolve():
    raise RuntimeError("Run this script with this project's .venv Python")

raise SystemExit(subprocess.call([
    "uv", "pip", "install", "--python", sys.executable,
    "-r", str(root / "requirements.txt"),
    "--extra-index-url", "https://pypi.nvidia.com",
    "--index-strategy", "unsafe-best-match",
    "--cache-dir", str(root / ".cache" / "uv"),
]))
