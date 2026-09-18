# The guide

Gesso has a lot of pages. This one tells you **which to read, and in what
order**, for whatever you are actually trying to do.

Everything here is a signpost. If you already know what you want, the sidebar
and the [reference](reference/core.md) are faster.

## If you have five minutes

```console
$ pip install -e .
$ gesso new myapp
$ cd myapp && python -m myapp
```

A window, wired up. [Quickstart](getting-started/quickstart.md) is the same
thing with the parts explained.

## Pick your way in

=== "I am starting a project"

    1. [Installation](getting-started/installation.md) — what to install, and
       which optional pieces you can skip.
    2. [Quickstart](getting-started/quickstart.md) — `gesso new`, and what it
       generates.
    3. [Application identity](concepts/application-identity.md) — the `AppSpec`,
       and why every path comes from it.
    4. Then [Tracker](examples/tracker.md), which is what a filled-in project
       looks like.

    **You do not need to read the concepts first.** The generated project is
    small, and reading it is faster than reading about it.

=== "I want to understand the design"

    Read [Architecture](concepts/architecture.md) first — the tier rule ("an
    application depends on Gesso; Gesso never depends on the application") and
    the Qt-free/optional-dependency boundaries explain almost every other
    decision in the SDK.

    Then the tier you are actually touching:

    | Tier | Concept | Reference |
    | ---- | ------- | --------- |
    | Identity and paths | [Application identity](concepts/application-identity.md) | [`gesso.core`](reference/core.md) |
    | Settings | [Configuration](concepts/configuration.md) | [`gesso.config`](reference/config.md) |
    | Translations | [Internationalisation](concepts/internationalisation.md) | [`gesso.i18n`](reference/i18n.md) |
    | Colours and styles | [Design system](concepts/design-system.md) | [`gesso.ui.theme`](reference/theme.md) |
    | Artwork | [Icons](concepts/icons.md) | [`gesso.ui.icons`](reference/icons.md) |
    | Controls | [Widgets](concepts/widgets.md) | [`gesso.ui.widgets`](reference/widgets.md) |
    | The window | [Application shell](concepts/application-shell.md) | [`gesso.ui.app`](reference/app.md) |

=== "I want to do one specific thing"

    | Goal | Go to |
    | ---- | ----- |
    | Store a setting | [Store a setting](tutorials/config.md) |
    | Stop a bad value getting in | [Defining a schema](guides/defining-a-schema.md) |
    | Choose a file format | [Choosing a config format](guides/config-formats.md) |
    | Cope with an old or broken config file | [Validating and migrating](guides/validating-and-migrating.md) |
    | Translate the interface | [Translate an application](tutorials/i18n.md) |
    | Make a theme | [Make a palette](tutorials/theming.md) |
    | Add my own artwork | [Ship your own icons](tutorials/icons.md) |
    | Build a settings pane | [Build a settings pane](tutorials/widgets.md) |
    | Build the window | [Build a windowed application](tutorials/shell.md) |
    | See it all together | [Tracker](examples/tracker.md) |

=== "I am learning by reading code"

    Read the four examples **in order**. Each rung adds a tier and keeps the one
    below it, so reading them adds up to reading Gesso's feature set:

    1. [Hello, Gesso](examples/hello-cli.md) — a schema and three formats.
    2. [Basket](examples/basket.md) — constraints, translations, plurals.
    3. [Gallery](examples/gallery.md) — a window, themes, widgets, icons.
    4. [Tracker](examples/tracker.md) — the shell, four pages, two languages.

    Rungs three and four are the pair worth studying: Gallery builds its own
    window, Tracker hands it to `AppShell`, and Tracker is **shorter** despite
    doing far more.

## Cover to cover

If you would rather just read straight through:

1. **[Getting started](getting-started/installation.md)** — install, and
   generate a project. Ten minutes.
2. **[Architecture](concepts/architecture.md)** — the one chapter that makes the
   rest obvious. Fifteen minutes.
3. **[Configuration](concepts/configuration.md)** +
   **[Translations](concepts/internationalisation.md)** — the two tiers that
   have nothing to do with Qt, and that a command-line tool can use on its own.
4. **[Tutorials](tutorials/index.md)** — do one, not all six. Pick the tier you
   are about to use; they are self-contained.
5. **[The design system](concepts/design-system.md)** +
   **[Widgets](concepts/widgets.md)** + **[Icons](concepts/icons.md)** — if you
   are building a GUI, these three are one chapter in spirit.
6. **[The application shell](concepts/application-shell.md)** — and then the
   [shell tutorial](tutorials/shell.md).
7. **[Examples](examples/index.md)** — read Tracker last, as a summary.
8. **[Reference](reference/core.md)** — for looking things up, not for reading.

## How the documentation is arranged

| Section | Kind of answer | Written for |
| ------- | -------------- | ----------- |
| [Getting started](getting-started/installation.md) | "How do I get running?" | doing it now |
| [Concepts](concepts/architecture.md) | "Why is it like this?" | understanding it |
| [Guides](guides/config-formats.md) | "How do I decide?" | choosing between options |
| [Tutorials](tutorials/index.md) | "How do I do this?" | following along |
| [Examples](examples/index.md) | "What does it look like when it works?" | reading code |
| [Reference](reference/core.md) | "What is the signature?" | looking it up |

The four in the middle overlap on purpose. A concept explains the design; a
guide explains the decision; a tutorial walks you through the mechanics; an
example shows the result. When they seem to repeat themselves, they are usually
answering different questions.

## Two things to know before you write anything

**The tier rule.** An application depends on Gesso. Gesso never depends on the
application. That is why there is no global singleton, why `AppContext` is
something you construct and pass, and why nothing under `gesso.core` or
`gesso.config` imports Qt.

**Nothing says "application".** There is no `Application` base class to
inherit, no plugin registry, and no framework lifecycle. Gesso supplies
identity, settings, translations, a design system and a window; your code is
everything else, and it stays ordinary Python. See
[Architecture](concepts/architecture.md).

## If something is missing

The [roadmap](roadmap.md) says what is planned and, more usefully, what is
deliberately *not*. Reach for the [contributing
guide](contributing.md) if you think something belongs here — the bar is
usually "does a second application need it?".
