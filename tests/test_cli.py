import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
INTERPRETER = ROOT / "sloperator.py"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(INTERPRETER), *args], capture_output=True, encoding="utf-8"
    )


def test_runs_a_file():
    completed = run_cli(str(ROOT / "examples/hello.slop"))
    assert completed.returncode == 0
    assert completed.stdout == "hello, slop\n"
    assert completed.stderr == ""


def test_tab_escape_prints_a_tab(tmp_path: Path):
    program = tmp_path / "tab.slop"
    program.write_text("hallucinate(“name\\tscore”)✨\n", encoding="utf-8")
    completed = run_cli(str(program))
    assert completed.returncode == 0
    assert completed.stdout == "name\tscore\n"
    assert completed.stderr == ""


def test_error_goes_to_stderr_after_earlier_output(tmp_path: Path):
    program = tmp_path / "boom.slop"
    program.write_text("hallucinate(“before”)✨\nhallucinate(missing)✨\n", encoding="utf-8")
    completed = run_cli(str(program))
    assert completed.returncode == 1
    assert completed.stdout == "before\n"
    assert completed.stderr == "SlopLang runtime error at line 2: undefined variable 'missing'\n"
    assert "Traceback" not in completed.stderr


def test_missing_file_and_usage():
    assert run_cli().returncode == 2
    missing = run_cli(str(ROOT / "nope.slop"))
    assert missing.returncode == 2
    assert "could not read" in missing.stderr


@pytest.mark.parametrize("flag_first", [True, False])
def test_check_does_not_execute(tmp_path: Path, flag_first: bool):
    program = tmp_path / "check.slop"
    program.write_text("hallucinate(“not printed”)✨\nhallucinate(missing)✨\n", encoding="utf-8")
    args = ["--check", str(program)] if flag_first else [str(program), "--check"]
    completed = run_cli(*args)
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


@pytest.mark.parametrize(
    ("source", "error"),
    [
        (
            'hallucinate("hi")✨',
            "SlopLang lexical error at line 1: "
            "straight quotes are not supported, use “ and ” for strings\n",
        ),
        (
            "hallucinate(“not printed”)✨\nslop x✨",
            "SlopLang syntax error at line 2: "
            "expected '=' after variable name, an initializer is required, found '✨'\n",
        ),
    ],
)
def test_check_reports_errors(tmp_path: Path, source: str, error: str):
    program = tmp_path / "invalid.slop"
    program.write_text(source, encoding="utf-8")
    completed = run_cli("--check", str(program))
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == error


def test_check_empty_file(tmp_path: Path):
    program = tmp_path / "empty.slop"
    program.write_text("", encoding="utf-8")
    completed = run_cli("--check", str(program))
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""


def test_check_missing_file_and_usage():
    assert run_cli("--check").returncode == 2
    assert run_cli("--check", "one.slop", "two.slop").returncode == 2
    missing = run_cli("--check", str(ROOT / "nope.slop"))
    assert missing.returncode == 2
    assert "could not read" in missing.stderr
