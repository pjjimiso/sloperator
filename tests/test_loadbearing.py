import pytest

from sloperator.runner import run_source


@pytest.mark.parametrize(
    ("initializer", "expected"),
    [
        ("42", "42"),
        ("0", "0"),
        ("-42", "-42"),
        ("- 42", "-42"),
        ("-0", "0"),
        ("9000000000000000000000000000001", "9000000000000000000000000000001"),
        ("“hello”", "hello"),
        ("✅", "✅"),
        ("❌", "❌"),
    ],
)
def test_literal_initializers(initializer: str, expected: str):
    result = run_source(f"loadbearing x = {initializer}✨ hallucinate(x)✨")
    assert (result.stdout, result.stderr, result.exit_code) == (f"{expected}\n", "", 0)


@pytest.mark.parametrize(
    "initializer",
    [
        "(42)",
        "(-42)",
        "-(42)",
        "--42",
        "-✅",
        "-❌",
        "-“hello”",
        "!✅",
        "1 + 2",
        "1 / 0",
        "“a” + “b”",
        "1 < 2",
        "✅ && ❌",
        "mutable",
        "CONSTANT",
        "missing",
        "hallucinate",
        "nothing",
        "nothing()",
        "hallucinate(“must not print”)",
    ],
)
def test_invalid_initializers_fail_at_runtime_without_evaluation(initializer: str):
    source = f"""slop mutable = 1✨
loadbearing CONSTANT = 2✨
clanker nothing() {{}}
hallucinate(“before”)✨
loadbearing x = {initializer}✨
hallucinate(“after”)✨"""
    result = run_source(source)
    assert result.stdout == "before\n"
    assert result.stderr == (
        "SlopLang runtime error at line 5: "
        "loadbearing initializer must be a literal or a negative number\n"
    )
    assert result.exit_code == 1


def test_invalid_initializer_does_not_call_user_function():
    result = run_source("""clanker side_effect() {
    hallucinate(“must not print”)✨
    ship 1✨
}
loadbearing x = side_effect()✨""")
    assert result.stdout == ""
    assert "loadbearing initializer must be" in result.stderr
    assert result.exit_code == 1


def test_unexecuted_invalid_declarations_and_assignments_are_allowed():
    result = run_source("""loadbearing x = 1✨
vibe ❌ {
    loadbearing invalid = (42)✨
    x = 2✨
}
clanker uncalled() {
    loadbearing invalid = hallucinate(“never”)✨
    x = 3✨
}
hallucinate(x)✨""")
    assert (result.stdout, result.stderr, result.exit_code) == ("1\n", "", 0)


@pytest.mark.parametrize(
    ("assignment", "output", "message"),
    [
        ("1", "", "cannot assign to loadbearing 'x'"),
        ("2", "", "cannot assign to loadbearing 'x'"),
        ("hallucinate(“RHS ran”)", "RHS ran\n", "cannot assign to loadbearing 'x'"),
        ("1 / 0", "", "division by zero"),
    ],
)
def test_reassignment_evaluates_rhs_before_rejection(assignment: str, output: str, message: str):
    result = run_source(f"loadbearing x = 1✨\nx = {assignment}✨")
    assert result.stdout == output
    assert result.stderr == f"SlopLang runtime error at line 2: {message}\n"
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "source",
    [
        "loadbearing x = 1✨\n{ x = 2✨ }",
        "loadbearing x = 1✨\nclanker f() { x = 2✨ } f()✨",
        "clanker f() { loadbearing x = 1✨\nvibe ✅ { x = 2✨ } } f()✨",
    ],
)
def test_reassignment_finds_enclosing_loadbearing_binding(source: str):
    result = run_source(source)
    assert result.stderr == "SlopLang runtime error at line 2: cannot assign to loadbearing 'x'\n"
    assert result.exit_code == 1


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("loadbearing x = 1✨", "loadbearing x = 2✨"),
        ("loadbearing x = 1✨", "slop x = 2✨"),
        ("slop x = 1✨", "loadbearing x = 2✨"),
        ("clanker x() {}", "loadbearing x = 2✨"),
        ("loadbearing x = 1✨", "clanker x() {}"),
    ],
)
def test_same_scope_redeclaration_is_rejected(first: str, second: str):
    result = run_source(f"{first}\n{second}")
    assert (
        result.stderr == "SlopLang runtime error at line 2: 'x' is already declared in this scope\n"
    )
    assert result.exit_code == 1


def test_mutable_redeclaration_still_evaluates_initializer_before_duplicate_check():
    result = run_source("loadbearing x = 1✨\nslop x = hallucinate(“initializer ran”)✨")
    assert result.stdout == "initializer ran\n"
    assert (
        result.stderr == "SlopLang runtime error at line 2: 'x' is already declared in this scope\n"
    )


def test_loadbearing_validation_precedes_duplicate_check():
    result = run_source("loadbearing x = 1✨\nloadbearing x = hallucinate(“never”)✨")
    assert result.stdout == ""
    assert result.stderr == (
        "SlopLang runtime error at line 2: "
        "loadbearing initializer must be a literal or a negative number\n"
    )


def test_shadowing_and_mutable_parameters():
    result = run_source("""loadbearing x = 1✨
{
    slop x = x + 1✨
    x = x + 1✨
    hallucinate(x)✨
}
{
    loadbearing x = 4✨
    hallucinate(x)✨
}
slop y = 5✨
{
    loadbearing y = 6✨
    hallucinate(y)✨
}
clanker bump(x) {
    x = x + 1✨
    ship x✨
}
hallucinate(bump(x))✨
hallucinate(x)✨
hallucinate(y)✨""")
    assert (result.stdout, result.stderr, result.exit_code) == ("3\n4\n6\n2\n1\n5\n", "", 0)


def test_constants_are_fresh_in_each_function_call_and_loop_iteration():
    result = run_source("""clanker f() {
    loadbearing local = 7✨
    ship local✨
}
slop i = 0✨
ralph i < 3 {
    loadbearing step = 1✨
    hallucinate(f())✨
    i = i + step✨
}
hallucinate(i)✨""")
    assert (result.stdout, result.stderr, result.exit_code) == ("7\n7\n7\n3\n", "", 0)


@pytest.mark.parametrize("name", ["f", "hallucinate"])
def test_existing_immutable_binding_diagnostic_is_preserved(name: str):
    result = run_source(f"clanker f() {{}}\n{name} = 1✨")
    assert result.stderr == (
        f"SlopLang runtime error at line 2: cannot assign to immutable binding '{name}'\n"
    )
    assert result.exit_code == 1
