"""Local, secret-free PAPER report/export and consistent SQLite backup."""

# ruff: noqa: E402 -- repository CLI imports the existing backend.

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from paper_journal import PaperJournal


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["report", "export", "backup"])
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    journal = PaperJournal()
    if args.action == "report":
        print(json.dumps(journal.report(), ensure_ascii=False, indent=2))
        return
    if args.output is None:
        parser.error("export and backup require --output")
    if args.output.resolve() == journal.path.resolve():
        parser.error("Output must differ from the active journal")
    if args.action == "backup":
        journal.backup(args.output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(dir=args.output.parent, prefix=".paper-export-")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(journal.export(args.format))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, args.output)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print("PAPER " + args.action + " saved: " + str(args.output))


if __name__ == "__main__":
    main()
