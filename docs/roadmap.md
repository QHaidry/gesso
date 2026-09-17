# Roadmap

What is built, what is next, and — importantly — what Gesso will not do.

## Available today

| Capability | Module |
| --- | --- |
| Application identity, XDG path resolution | `gesso.core` |
| Typed schemas, validation | `gesso.config` |
| JSON / TOML / YAML codecs, conversion | `gesso.config` |
| Translation catalogs, language detection, direction | `gesso.i18n` |
| Token contract, base stylesheet, palettes, theming | `gesso.ui.theme` |
| SVG icons rendered and tinted at runtime | `gesso.ui.icons` |
| Widget primitives, styled by object name | `gesso.ui.widgets` |
| Application bootstrap and window shell | `gesso.ui.app` |

## Next

The order is deliberate: each tier is proven by an application before the next
one is designed.

### 1. Project generator

The library is complete enough to build an application with, and this is the
piece that turns it from a library into an SDK.

`gesso new myapp` — a scaffold with everything already wired: entry points,
packaging, CI, tests, a theme, translations and a settings schema, so a new
project starts from a working application rather than an empty directory.

### 2. Larger widget composites — `gesso.ui.widgets`

The primitives are in. What is deliberately *not* here:

- **Composites** — `NavSidebar`, `SettingsExplorer`, `ThumbnailGrid`,
  `SearchField`, `Callout`
- **Dialogs** — `info`, `warning`, `critical`, `confirm`, `FormDialog`
- **`SettingsPage`** — driven by a schema, so declaring your options gives you a
  complete settings UI

These wait for a second application to need the same shape. The primitives were
safe to build because the base stylesheet already named them; composites would
mean designing an API for a shape nobody has built yet.

### 3. Migrations

A declarative schema-version mechanism, replacing the explicit
[manual migrations](guides/validating-and-migrating.md#migrating) used today.

### 4. An optional internationalisation backend

Two things `gesso.i18n` deliberately does not do, because doing them properly
needs real CLDR data and guessing is worse than waiting:

- **Plural rules.** English's one/other split is not how Polish, Arabic or
  Russian work.
- **Locale-aware number and date formatting.** `1234567.89` is written
  differently in Germany, India and the United States.

These ship as an **optional extra**, so the dependency-free core stays
dependency-free. The catalog contract is already narrow —
`catalog(language) -> dict` — so a gettext or Qt `.qm` backend can be added
without changing the public API.

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
  including in tests — and there is no process-wide `Translator` either.
- **No domain code.** If it is specific to your product, it belongs to your
  product.
- **No framework lock-in.** Gesso is a library you call; it does not run your
  application for you.
