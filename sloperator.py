import argparse
import sys
from pathlib import Path

from sloperator.runner import run_program


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="uv run sloperator.py")
    parser.add_argument("--check", action="store_true", help="check syntax without executing")
    parser.add_argument("file", metavar="<file.slop>")
    args = parser.parse_args(argv[1:])

    path = Path(args.file)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as error:
        print(f"could not read '{path}': {error.strerror}", file=sys.stderr)
        return 2

    error = run_program(source, sys.stdout, check=args.check)
    if error is not None:
        sys.stdout.flush()
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
