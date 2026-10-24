"""PostToolUse hook: sorts imports and formats a .py file in this repo after Claude edits it."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    file_path = json.load(sys.stdin).get('tool_input', {}).get('file_path', '')
    if not file_path.endswith('.py'):
        return
    path = Path(file_path).resolve()
    if ROOT not in path.parents:
        return
    ruff = [sys.executable, '-m', 'ruff']
    subprocess.run([*ruff, 'check', '--select', 'I', '--fix', '--quiet', str(path)], cwd=ROOT)
    subprocess.run([*ruff, 'format', '--quiet', str(path)], cwd=ROOT)


if __name__ == '__main__':
    main()
