import pytest

from sloperator.runner import run_source


@pytest.mark.parametrize("expression", ["1 + 2 * 3", "2 * 3 + 1"])
def test_multiplication_happens_before_addition(expression: str):
    result = run_source(f"hallucinate({expression})✨")

    assert result.exit_code == 0
    assert result.stderr == ""
    assert result.stdout == "7\n"
