import pytest

from sloperator.errors import LexicalError
from sloperator.lexer import tokenize


@pytest.mark.parametrize(
    ("source", "character", "line"),
    [
        ("@", "@", 1),
        ("\n\n@", "@", 3),
        ("slop x = 1✨\n$", "$", 2),
    ],
)
def test_unexpected_character_raises_lexical_error(source: str, character: str, line: int):
    with pytest.raises(LexicalError) as info:
        tokenize(source)

    message = f"unexpected character '{character}'"
    assert info.value.line == line
    assert info.value.message == message
    assert str(info.value) == f"SlopLang lexical error at line {line}: {message}"
