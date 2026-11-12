# Sloperator

A tree-walking interpreter for SlopLang, written in Python. See the [language specification](docs/spec.md) for syntax, semantics, and examples.

## Run and validate

```bash
uv run sloperator.py examples/fib.slop         # run a program
uv run sloperator.py --check examples/fib.slop # check syntax without executing
uv run pytest                                # tests
uv run ruff format --check                    # formatting
uv run ruff check                             # linting
uv run ty check                               # type checking
uv run playground/server.py                   # start the playground
```

Open the playground at <http://localhost:8080>.

## Layout

| Path                    | What it is                                            |
| ----------------------- | ----------------------------------------------------- |
| `sloperator.py`         | Command-line entrypoint                               |
| `sloperator/lexer/`     | Source text to tokens                                 |
| `sloperator/parser/`    | Tokens to AST (`ast.py` holds the node definitions)    |
| `sloperator/evaluator/` | Walks the AST: values, environments, the interpreter   |
| `sloperator/runner.py`  | Runs source through all three stages                  |
| `docs/spec.md`          | The language specification                            |
| `examples/`            | Example programs                                      |
| `tests/`               | Pytest suite                                          |
| `playground/`          | A tiny web server and editor page for running programs |
