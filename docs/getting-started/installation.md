# Installation

## Requirements

| Requirement | Version | Notes |
| --- | --- | --- |
| Python | 3.9 or newer | 3.11+ gives you TOML reading from the standard library |
| PySide6 | 6.5 or newer | Only needed for the Qt layer (`gesso.ui`) |

Gesso's core has **no runtime dependencies at all**.

## Install

```bash
pip install gesso-sdk
```

That gives you `gesso.core` and `gesso.config` with JSON support.

!!! note "Why isn't the package called `gesso`?"

    The distribution is named **`gesso-sdk`** because the name `gesso` on PyPI
    is held by an unrelated, dormant project, as are `gesso` on crates.io (a
    Rust Wayland wallpaper daemon) and npm (an Acro Media design system).

    **The import name is `gesso`** — `import gesso` is what you write in code.

## Optional extras

Each heavier capability is opt-in, so a command-line tool never drags in Qt.

=== "TOML"

    Needed both to *read* and to *write* TOML. On Python 3.11+ reading uses the
    standard library, but writing always needs `tomli-w`.

    ```bash
    pip install "gesso-sdk[toml]"
    ```

=== "YAML"

    ```bash
    pip install "gesso-sdk[yaml]"
    ```

=== "Qt interface"

    ```bash
    pip install "gesso-sdk[gui]"
    ```

=== "Everything"

    ```bash
    pip install "gesso-sdk[toml,yaml,gui]"
    ```

!!! tip "A missing extra is never a surprise"

    If a configuration file exists in a format whose backend is not installed,
    Gesso tells you exactly what to install rather than failing obscurely:

    ```
    error: found /home/you/.config/myapp/config.toml but writing TOML requires
    the 'tomli-w' package (pip install 'gesso-sdk[toml]')
    ```

    What it will *not* do is quietly create a second configuration file in a
    different format next to the one it could not read.

## Install from source

```bash
git clone https://github.com/QHaidry/gesso.git
cd gesso
python -m venv venv && source venv/bin/activate
pip install -e ".[dev,docs]"
```

## Verify

```bash
python -c "import gesso; print(gesso.__version__)"
```

## Next

[:octicons-arrow-right-24: Quickstart](quickstart.md)
