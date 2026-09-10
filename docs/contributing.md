# Contributing

Gesso is a small SDK by Quoxiom. Changes should be focused and friendly.

## Development setup

```bash
git clone https://github.com/quoxiom/gesso.git
cd gesso
python -m venv venv && source venv/bin/activate
pip install -e ".[dev,docs]"
```

## Running the tests

```bash
pytest                       # everything
pytest tests/test_store.py   # one file
pytest -k convert            # by name
```

The suite should be green before you push. Two tests skip when `tomli-w` is
absent; installing the `dev` extra gives you full coverage, including the TOML
write path and the TOML-only branches of discovery.

## Building the docs

```bash
mkdocs serve    # live preview at http://127.0.0.1:8000
mkdocs build --strict
```

`--strict` is the real check: it turns warnings into failures, so a broken
internal link or a missing snippet file will stop the build. Run it before
pushing.

## Conventions

### Layering

The rule in [Architecture](concepts/architecture.md#the-dependency-rule) is not
a guideline:

> An application depends on Gesso. Gesso never depends on the application.

Concretely: **no module in `gesso` may import from an application**, and
`gesso.core` and `gesso.config` must not import Qt. If you find yourself needing
an application's name, take an `AppSpec` instead.

### Dependencies

Keep the core dependency-free. A new third-party import belongs behind an
optional extra, and its codec or feature must degrade with an actionable
`unavailable_reason()` rather than an `ImportError` at an unrelated place.

### Style

- Type hints on public functions.
- 100-column lines, `black` formatting.
- Docstrings explain *why*, not *what* — the code already says what.
- Comments are for the non-obvious: a specification quirk, a workaround, a
  deliberate refusal.

## Documentation is part of the contract

An SDK is its documentation. Two rules keep the two from drifting apart:

1. **Examples are executed.** `examples/hello.py` is driven by
   `tests/test_example.py`, and the guide embeds the *real file* via
   `pymdownx.snippets`. If the example breaks, the docs are wrong and the suite
   says so.
2. **`mkdocs build --strict` must pass.** Snippets use `check_paths`, so a typo
   in an embedded path fails the build rather than silently rendering nothing.

If you change a public API, update the matching page under `docs/reference/`.

## Adding a codec

1. Subclass `Codec` in `gesso/config/codecs.py`, defining `name`, `extensions`,
   `loads` and `dumps`.
2. Gate it with `available()` / `unavailable_reason()`, naming the package to
   install.
3. Add it to the `_CODECS` tuple and, if it should win ties, to
   `DISCOVERY_PRECEDENCE`.
4. Add the dependency as an optional extra in `pyproject.toml`, and to `dev` so
   the tests always run it.
5. Extend `tests/test_codecs.py`.

Because the schema is codec-independent, nothing else needs to change — that is
the point of the split.

## Reporting and proposing

- **Bugs and feature requests** — open an [issue](https://github.com/quoxiom/gesso/issues).
- **Code** — fork, branch, and open a [pull request](https://github.com/quoxiom/gesso/pulls).

## License

MIT. By contributing you agree your work is licensed under the same terms.
