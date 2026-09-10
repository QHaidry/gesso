# `gesso.core`

Application identity and path resolution. **Standard library only** — importing
`gesso.core` never pulls in a third-party package.

```python
from gesso.core import AppContext, AppPaths, AppSpec, slugify
```

## `AppSpec`

```python
@dataclass(frozen=True)
class AppSpec:
    name: str
    app_id: str = ""
    org: str = ""
    version: str = "0.0.0"
    display_name: str = ""
    description: str = ""
    default_config_format: str = "json"
    config_stem: str = "config"
```

A description of an application. Frozen: once constructed it cannot be mutated.

| Field | Default | Notes |
| --- | --- | --- |
| `name` | *required* | Must not be blank, or `ValueError` is raised |
| `app_id` | `slugify(name)` | Directory name under each XDG base |
| `org` | `""` | Organisation, for desktop integration |
| `version` | `"0.0.0"` | |
| `display_name` | `name` | |
| `description` | `""` | |
| `default_config_format` | `"json"` | Format created when no config exists |
| `config_stem` | `"config"` | Filename stem, before the extension |

```python
>>> AppSpec("My Fancy App").app_id
'my-fancy-app'
>>> AppSpec("My App", app_id="myapp", version="1.2.0").app_id
'myapp'
>>> AppSpec("   ")
ValueError: AppSpec.name must not be empty
```

## `AppContext`

```python
class AppContext:
    def __init__(self, spec: AppSpec, paths: AppPaths | None = None) -> None
```

An `AppSpec` bound to a resolved `AppPaths`. This is the handle the rest of
Gesso accepts. When `paths` is omitted, the real XDG directories are used.

### Properties

| Name | Returns |
| --- | --- |
| `spec` | The original `AppSpec` |
| `paths` | The bound `AppPaths` |
| `app_id` | `spec.app_id` |
| `name` | `spec.name` |
| `config_dir` | `paths.config_dir` |
| `data_dir` | `paths.data_dir` |
| `cache_dir` | `paths.cache_dir` |
| `state_dir` | `paths.state_dir` |

### Methods

| Signature | Returns |
| --- | --- |
| `config_file(extension: str \| None = None)` | `config_dir / f"{config_stem}.{extension or default_config_format}"`. A leading dot in `extension` is optional. |

```python
>>> context.config_file()
PosixPath('/home/you/.config/myapp/config.json')
>>> context.config_file("toml")
PosixPath('/home/you/.config/myapp/config.toml')
```

## `AppPaths`

```python
@dataclass(frozen=True)
class AppPaths:
    app_id: str
    config_home: Path
    data_home: Path
    cache_home: Path
    state_home: Path
```

The XDG directories for one application. The base directories are stored
explicitly rather than read from the environment on each access, which is what
makes isolated profiles possible.

### `AppPaths.resolve`

```python
@classmethod
def resolve(
    cls,
    app_id: str,
    *,
    config_home: Path | None = None,
    data_home: Path | None = None,
    cache_home: Path | None = None,
    state_home: Path | None = None,
) -> AppPaths
```

Builds a layout, defaulting any base you do not supply to the real XDG
directory. Raises `ValueError` if `app_id` is empty.

### Properties

| Name | Returns |
| --- | --- |
| `config_dir` | `config_home / app_id` |
| `data_dir` | `data_home / app_id` |
| `cache_dir` | `cache_home / app_id` |
| `state_dir` | `state_home / app_id` |

### Methods

| Signature | Returns |
| --- | --- |
| `all_dirs()` | `(config_dir, data_dir, cache_dir, state_dir)`, in that order |
| `ensure()` | Creates every per-application directory (`mkdir(parents=True, exist_ok=True)`) |
| `subdir(base, *parts)` | A path under one of `"config"`, `"data"`, `"cache"`, `"state"`; `ValueError` otherwise |

```python
>>> paths.subdir("config", "themes")
PosixPath('/home/you/.config/myapp/themes')
```

## Functions

### `xdg_config_home()`, `xdg_data_home()`, `xdg_cache_home()`, `xdg_state_home()`

Return the corresponding XDG base directory as a `Path`.

| Variable | Default |
| --- | --- |
| `XDG_CONFIG_HOME` | `~/.config` |
| `XDG_DATA_HOME` | `~/.local/share` |
| `XDG_CACHE_HOME` | `~/.cache` |
| `XDG_STATE_HOME` | `~/.local/state` |

Following the specification: an **unset or empty** variable falls back to the
default, and a **relative** path is ignored rather than resolved against the
current working directory.

### `slugify(name)`

```python
slugify("My Fancy App")   # 'my-fancy-app'
slugify("!!!")            # 'app'
```

Reduces a name to a lowercase, hyphen-separated identifier: runs of anything
that is not `a-z0-9` collapse to a single `-`, and an empty result becomes
`"app"`.
