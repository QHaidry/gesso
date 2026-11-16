# Gesso

> *Gesso* — the primer layer a painter applies before the artwork.

Gesso is an SDK for building Qt (PySide6) desktop applications on Linux. It
provides the pieces every application needs but nobody wants to write twice:

- **Design system** — a token contract plus a generic, token-driven stylesheet *(planned)*
- **Theming** — swappable JSON palettes, with built-in and user overrides *(planned)*
- **Internationalisation** — JSON catalogs, language detection, three-layer override, English fallback
- **Configuration** — a schema-typed, atomic store supporting JSON, TOML and YAML
- **Widget library** — standard Qt widgets styled by the design system *(planned)*
- **Application shell** — window bootstrap, navigation, status bar *(planned)*

Gesso is organised in tiers so a headless CLI pays for none of the Qt weight:

| Tier | Import | Requires |
|------|--------|----------|
| Core | `gesso.core` | stdlib only |
| Headless features | `gesso.config`, `gesso.i18n` | stdlib (+ optional codecs) |
| Qt UI | `gesso.ui` | `PySide6` (`gesso-sdk[gui]`) |

## Why is it called Gesso?

Muralis — the first application built on Gesso — means *"of the wall"*. Gesso is
the primer you apply to the wall before the mural: the base layer that makes
everything painted on top of it consistent.

## Status

Pre-alpha. The core, configuration and internationalisation layers are in
place; the Qt tiers have not been started. See [`docs/`](docs/) for the design
and the [roadmap](docs/roadmap.md) for what is next.

## Installation

```bash
pip install gesso-sdk            # core, JSON config only
pip install "gesso-sdk[toml]"    # + TOML support
pip install "gesso-sdk[yaml]"    # + YAML support
pip install "gesso-sdk[gui]"     # + Qt widgets (PySide6)
```

> The distribution is named `gesso-sdk` because the `gesso` name on PyPI is
> held by an unrelated, dormant project. The **import name is `gesso`**.

## License

MIT — Copyright (c) 2026 Qamber Haidry.
