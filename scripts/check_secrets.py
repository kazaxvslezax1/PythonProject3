"""Scan tracked source without opening secret files; never print matching values."""

import re
import subprocess
from pathlib import Path

PATTERNS = [
    re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def main():
    names = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    failures = []
    for name in filter(None, names):
        path = Path(name)
        parts = set(path.parts)
        forbidden = (
            (path.name.startswith(".env") and path.name != ".env.example")
            or bool(parts & {".venv", "venv", "runtime", "__pycache__"})
            or path.suffix in (".key", ".pem")
        )
        if forbidden:
            failures.append(name + ": forbidden tracked file (not opened)")
            continue
        if path.suffix not in (".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json") or not path.is_file():
            continue
        for number, line in enumerate(path.read_text(errors="replace").splitlines(), 1):
            if any(pattern.search(line) for pattern in PATTERNS):
                failures.append(f"{name}:{number}: possible secret (redacted)")
    print(
        "\n".join(failures)
        if failures
        else "Tracked-source secret scan passed; secret files were not opened."
    )
    return bool(failures)


if __name__ == "__main__":
    raise SystemExit(main())
