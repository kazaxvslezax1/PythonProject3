import ast
import re
from pathlib import Path


def test_no_embedded_provider_credentials():
    pattern = re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b|\bsk-[A-Za-z0-9_-]{20,}\b")
    for path in Path("backend").glob("*.py"):
        assert not pattern.search(path.read_text()), f"Credential in {path}"


def test_python_sources_parse():
    for path in Path("backend").glob("*.py"):
        ast.parse(path.read_text(), filename=str(path))
