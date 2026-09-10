# Roadmap

What is built, what is next, and — importantly — what Gesso will not do.

## Available today

| Capability | Module |
| --- | --- |
| Application identity, XDG path resolution | `gesso.core` |
| Typed schemas, validation | `gesso.config` |
| JSON / TOML / YAML codecs, conversion | `gesso.config` |

## Next

The order is deliberate: each tier is proven by an application before the next
one is designed.

### 1. Internationalisation — `gesso.i18n`

- JSON translation files, user-overridable, English fallback
- Locale detection from `LANGUAGE`, `LC_ALL`, `LC_MESSAGES`, `LANG`
- A **domain** concept, so Gesso owns `gesso.*` keys and your application owns
  its own without collisions
- Locale-aware number and date formatting
- RTL support flag

JSON is kept as the format — it is CLI-friendly and trivially overridable — but
the backend will be pluggable, so gettext or Qt's `.qm` files can be added later
for plural forms, which JSON handles poorly.

### 2. Design system and theming — `gesso.ui.theme`

- A **token contract**: surfaces, text, accent, borders, typography, spacing
- A generic, token-driven base stylesheet
- `ThemeManager` with built-in themes plus user overrides
- A `themeChanged` signal, so themed widgets re-tint themselves instead of
  needing manual updates
- SVG icon set with runtime tinting

A design system is a *contract*, not a stylesheet — so a missing token will be
reported with the token's name rather than silently collapsing the UI to the
platform default.

### 3. Standard widget library — `gesso.ui.widgets`

The largest piece, and the one that does not exist in any form today:

- **Primitives** — `IconButton`, `ToggleButton`, `SegmentedControl`, `Card`,
  `PageHeader`, `SettingRow`, `SearchField`, `Callout`
- **Composites** — `NavSidebar`, `SettingsExplorer`, `ThumbnailGrid`,
  `EmptyState`, `StatusBar`
- **Dialogs** — `info`, `warning`, `critical`, `confirm`, `FormDialog`
- **`SettingsPage`** — driven by a schema, so declaring your options gives you a
  complete settings UI

### 4. Application shell — `gesso.ui.app`

- `run_app(spec, window_factory)`: `QApplication` metadata, high-DPI, palette
  *and* stylesheet, translator installation, exception hook
- `AppShell`: collapsible sidebar, navigation, content stack, status bar
- System tray and desktop notifications

### 5. Project generator

`gesso new myapp` — a scaffold with all of the above already wired: entry points,
packaging, CI, tests, theme, translations and a settings schema, so a new project
starts from a working application rather than an empty directory.

### 6. Migrations

A declarative schema-version mechanism, replacing the explicit
[manual migrations](guides/validating-and-migrating.md#migrating) used today.

## Adjacent, not yet scheduled

Broadly useful, but outside the original five features. Candidates for an
optional `gesso.extras` layer:

- Systemd user timers / cron scheduling
- Storage retention and cleanup
- Downloads with proxies and retries
- Desktop notifications

## What Gesso will not do

Stating this keeps the SDK from bloating:

- **No plugin framework.** Extension is constructor arguments and subclassing.
- **No global application singleton.** `AppContext` is something you construct,
  including in tests.
- **No domain code.** If it is specific to your product, it belongs to your
  product.
- **No framework lock-in.** Gesso is a library you call; it does not run your
  application for you.
