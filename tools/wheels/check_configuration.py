"""Check effective wheel settings using the exact cibuildwheel action version."""
from pathlib import Path
import re
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parents[2]
    action = (root / ".github/actions/build-wheels/action.yml").read_text(encoding="utf-8")
    pins = re.findall(r"uses:\s+pypa/cibuildwheel@v(\d+\.\d+\.\d+)\s*$", action, re.MULTILINE)
    if len(pins) != 1:
        raise ValueError("Expected one exact cibuildwheel action version")
    subprocess.run([sys.executable, "-m", "pip", "install", "--index-url", "https://pypi.org/simple",
                    "cibuildwheel==" + pins[0], "PyYAML==6.0.3", "pytest==8.3.5"], check=True)
    subprocess.run([sys.executable, "-m", "pytest", str(root / "tools/wheels/test_cibuildwheel_configuration.py"),
                    "-v"], check=True)


if __name__ == "__main__":
    main()
