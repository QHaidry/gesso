# Application identity

## The problem this solves

Most small applications hard-code where their files live:

```python
CONFIG_PATH = Path.home() / ".config" / "myapp" / "config.json"
WALLPAPER_DIR = Path.home() / "Pictures" / "MyApp"
```

It works right up until it doesn't. The application cannot be tested without
touching the developer's real home directory. It cannot be run with a throwaway
profile. A second application cannot reuse a line of it. And the day the name
changes, the paths are wrong in a dozen files.

Gesso replaces all of that with one declaration.

## `AppSpec` — who the application is

```python
--8<-- "examples/hello.py:39:45"
```

| Field | Type | Default | Meaning |
| --- | --- | --- | --- |
| `name` | `str` | *required* | Human-readable name, e.g. `"Gesso Hello"` |
| `app_id` | `str` | slug of `name` | Directory name, window class, systemd unit |
| `org` | `str` | `""` | Organisation, for desktop integration |
| `version` | `str` | `"0.0.0"` | Application version |
| `display_name` | `str` | `name` | Name shown in the UI |
| `description` | `str` | `""` | One-line description |
| `default_config_format` | `str` | `"json"` | Format used when creating a config |
| `config_stem` | `str` | `"config"` | Filename stem, before the extension |

`AppSpec` is a **frozen** dataclass: once built it cannot be mutated, so nothing
can quietly rewrite your application's identity halfway through a run.

`app_id` is derived from `name` when you do not supply it:

```python
>>> from gesso.core import AppSpec, slugify
>>> AppSpec("My Fancy App").app_id
'my-fancy-app'
>>> slugify("Muralis")
'muralis'
```

!!! tip "Use an explicit `app_id`"

    Slugifying is a convenience for examples and tests. A real application
    should state its id, because changing it later moves the user's files:

    ```python
    AppSpec(name="Muralis", app_id="muralis", org="Acme", version="0.4.0")
    ```

## `AppPaths` — where the files go

Gesso follows the [XDG Base Directory specification](https://specifications.freedesktop.org/basedir-spec/latest/).

| Property | Base | Default | Holds |
| --- | --- | --- | --- |
| `config_dir` | `$XDG_CONFIG_HOME` | `~/.config` | Settings, themes, locale overrides |
| `data_dir` | `$XDG_DATA_HOME` | `~/.local/share` | Durable application data |
| `cache_dir` | `$XDG_CACHE_HOME` | `~/.cache` | Regenerable caches |
| `state_dir` | `$XDG_STATE_HOME` | `~/.local/state` | Logs, session state |

Each is the base **joined with `app_id`**:

```mermaid
flowchart LR
    H["$XDG_CONFIG_HOME<br/><small>~/.config</small>"]
    A["app_id<br/><small>myapp</small>"]
    R["~/.config/myapp"]
    H --> A --> R
```

```console
$ tree --dirsfirst ~/.config/myapp ~/.cache/myapp
~/.config/myapp
├── config.json
└── themes/
~/.cache/myapp
└── thumbnails/
```

Three specification details Gesso gets right, because they are easy to get
wrong:

- An **unset** variable falls back to the default.
- An **empty** variable falls back to the default (not to `""`).
- A **relative** path is ignored, because the specification requires an
  absolute one. Gesso will not silently resolve `config` against your current
  working directory.

## `AppContext` — the two, bound together

`AppContext` pairs an `AppSpec` with its resolved `AppPaths`. This is the object
the rest of Gesso accepts, so no other module ever has to know how to find your
files.

```python
from gesso.core import AppContext, AppSpec

context = AppContext(AppSpec("My App", app_id="myapp"))

context.app_id      # 'myapp'
context.config_dir  # PosixPath('/home/you/.config/myapp')
context.config_file()          # .../config.json   (uses default_config_format)
context.config_file("toml")    # .../config.toml
```

### Isolated profiles

Because the base directories are stored on `AppPaths` rather than read from the
environment on every access, you can point an application at a throwaway tree
**without mutating `os.environ`** — which is what makes Gesso testable:

```python
from pathlib import Path

from gesso.core import AppContext, AppSpec
from gesso.core.paths import AppPaths

spec = AppSpec("My App", app_id="myapp")
paths = AppPaths.resolve(spec.app_id, config_home=Path("/tmp/profile-a"))
context = AppContext(spec, paths)

assert context.config_dir == Path("/tmp/profile-a/myapp")
```

Two contexts built this way never collide, so tests can run in parallel and
without cleaning up after themselves.

## Next

[:octicons-arrow-right-24: Configuration](configuration.md)
