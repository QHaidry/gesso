# `gesso.generator` and the `gesso` command

Scaffolding a new project. **No Qt needed** — the generator writes files.

```bash
gesso new myapp
```

```python
from gesso.generator import create, plan
```

## The `gesso` command

```bash
gesso new PATH [--name NAME] [--app-id ID] [--org ORG] [--description TEXT] [--overwrite]
gesso --version
```

| Option | Meaning |
| --- | --- |
| `PATH` | Where to write the project |
| `--name` | The display name. Defaults to the directory name |
| `--app-id` | The application id. Defaults to a slug of the name |
| `--org` | The organisation, for desktop integration |
| `--description` | A one-line description |
| `--overwrite` | Write into a directory that is not empty |

A directory that already has something in it is refused without
`--overwrite`: writing a scaffold over an existing project is never what was
meant.

## What you get

```
myapp/
├── pyproject.toml          # packaging, entry point, pytest config
├── README.md
├── .gitignore
├── src/myapp/
│   ├── app.py              # the AppSpec, context and translator
│   ├── config.py           # the settings schema
│   ├── home.py             # a page
│   ├── main.py             # run_app, and `build`
│   ├── locales/en.json
│   └── themes/default.json
└── tests/
    ├── conftest.py         # Qt on the offscreen platform
    └── test_app.py
```

**Every generated project runs, and its tests pass, before it is written.** The
generator's own test suite generates a project into a temporary directory and
runs its suite in a subprocess, because a scaffold that merely *looks*
plausible is worse than none: a new project's first experience becomes
debugging somebody else's boilerplate.

## `plan` and `create`

```python
from gesso.core import AppSpec

spec = AppSpec("My App", app_id="my-app", org="Acme")

for path, text in plan(spec):        # nothing is written
    print(path)

create(spec, "myapp")                # or write it
```

| Function | Description |
| --- | --- |
| `plan(spec, *, year=None)` | The files a scaffold would write, as `(path, text)`, without touching disk |
| `create(spec, directory, *, year=None, overwrite=False)` | Write them; returns the paths written |
| `render(text, values)` | Substitute `${name}` placeholders |
| `values_for(spec, *, year=None)` | The substitutions used |
| `TEMPLATES` | The `(template, destination)` pairs |
| `TEMPLATE_DIR` | Where the templates live in the package |

`plan` is separate from `create` so a caller — or a test — can inspect a project
before anything is written.

## Writing a template

Templates live in `gesso/templates/` and are rendered with `string.Template`:

| Placeholder | Value |
| --- | --- |
| `${name}` | The display name |
| `${app_id}` | The application id, e.g. `my-app` |
| `${package}` | The Python package, e.g. `my_app` |
| `${org}` | The organisation |
| `${version}` | The version |
| `${description}` | The description |
| `${year}` | The current year |

A destination may contain a placeholder too — that is how one template tree
lands in a package named after the application.

!!! warning "A literal dollar sign must be doubled"

    `string.Template` treats `$` as the start of a placeholder, so a template
    containing a bare `$` — a regular expression anchor, say — fails to render.
    Write `$$` for a literal one. That is a deliberate trade: the failure is
    loud and at generation time, rather than a silently mangled project.

## Exceptions

| Exception | Raised when |
| --- | --- |
| `ScaffoldError` | A template is missing or malformed, a placeholder is unfilled, or the target directory is not empty |
