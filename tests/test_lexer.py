import pytest

from sloperator.errors import LexicalError
from sloperator.lexer import Token, TokenType, tokenize


def types(source: str) -> list[TokenType]:
    return [token.type for token in tokenize(source)]


def test_keywords_operators_and_emoji():
    assert types("slop x = ✅ && !❌✨") == [
        TokenType.SLOP,
        TokenType.IDENTIFIER,
        TokenType.EQUAL,
        TokenType.TRUE,
        TokenType.AND,
        TokenType.BANG,
        TokenType.FALSE,
        TokenType.SPARKLES,
        TokenType.EOF,
    ]


def test_two_character_operators_are_greedy():
    assert types("== != <= >= ||") == [
        TokenType.EQUAL_EQUAL,
        TokenType.BANG_EQUAL,
        TokenType.LESS_EQUAL,
        TokenType.GREATER_EQUAL,
        TokenType.OR,
        TokenType.EOF,
    ]


def test_variation_selector_after_emoji_is_absorbed():
    tokens = tokenize("✅️✨️")
    assert [t.type for t in tokens] == [TokenType.TRUE, TokenType.SPARKLES, TokenType.EOF]
    assert tokens[0].lexeme == "✅️"


def test_number_literal_is_an_int():
    assert tokenize("9001")[0] == Token(TokenType.NUMBER, "9001", 9001, 1)


def test_hallucinate_is_an_identifier_not_a_keyword():
    assert tokenize("hallucinate")[0].type is TokenType.IDENTIFIER


def test_loadbearing_is_a_case_sensitive_keyword_with_identifier_boundaries():
    assert types("loadbearing loadbearing_x loadbearing1 Loadbearing") == [
        TokenType.LOADBEARING,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_identifiers_can_contain_digits_after_the_first_character():
    tokens = tokenize("x1 slop2 _3x 1x")
    assert [(token.type, token.lexeme) for token in tokens[:-1]] == [
        (TokenType.IDENTIFIER, "x1"),
        (TokenType.IDENTIFIER, "slop2"),
        (TokenType.IDENTIFIER, "_3x"),
        (TokenType.NUMBER, "1"),
        (TokenType.IDENTIFIER, "x"),
    ]


def test_string_may_contain_em_dash_and_opening_quote():
    assert tokenize("“x — “y”")[0].literal == "x — “y"


def test_tab_escape_is_decoded():
    assert tokenize(r"“name\tscore”")[0].literal == "name\tscore"


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ("\n\n@", 3),
        ("— comment\n@", 2),
        ("— first\n\n— third\n@\n", 4),
        ("slop x = 1✨ — inline comment\n@", 2),
    ],
)
def test_error_line_counts_comments_and_blank_lines(source: str, line: int):
    with pytest.raises(LexicalError) as info:
        tokenize(source)
    assert str(info.value) == f"SlopLang lexical error at line {line}: unexpected character '@'"


@pytest.mark.parametrize(
    ("source", "line"),
    [
        ("— comment", 1),
        ("— comment\n", 2),
        ("— first\n\n— third\nx", 4),
    ],
)
def test_token_lines_count_comments_and_blank_lines(source: str, line: int):
    assert all(token.line == line for token in tokenize(source))


@pytest.mark.parametrize(
    ("source", "line", "message"),
    [
        ('"hi"', 1, "straight quotes are not supported, use “ and ” for strings"),
        ("x;", 1, "semicolons are not supported, end statements with ✨"),
        ("\n// nope", 2, "comments start with an em dash (—), not //"),
        ("– nope", 1, "'–' is an en dash, comments start with an em dash (—)"),
        ("x”", 1, "unexpected closing quote ” without an opening “"),
        ("“abc", 1, "unterminated string"),
        ("“abc\n”", 1, "unterminated string"),
        ("“a\\q”", 1, "unknown escape sequence '\\q'"),
        ("“a\\", 1, "unterminated string"),
        ("a & b", 1, "unexpected character '&', did you mean '&&'?"),
        ("a | b", 1, "unexpected character '|', did you mean '||'?"),
    ],
)
def test_lexical_errors(source: str, line: int, message: str):
    with pytest.raises(LexicalError) as info:
        tokenize(source)
    assert info.value.line == line
    assert info.value.message == message
    assert str(info.value) == f"SlopLang lexical error at line {line}: {message}"
