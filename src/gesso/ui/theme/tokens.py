"""The design-token contract.

A design system is a *contract*, not a stylesheet. The contract says which
names exist, what each one means, and what happens when one is missing; a
stylesheet is merely one consumer of it.

Keeping the contract first is what makes a missing token a *reported problem*
rather than a stylesheet that quietly loses a rule and an interface that
collapses to the platform default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

__all__ = ["Token", "TokenContract", "BASE_CONTRACT", "TOKEN_GROUPS"]


@dataclass(frozen=True)
class Token:
    """One design token: a name, a last-resort value, and what it is for."""

    key: str
    default: str
    group: str = "misc"
    description: str = ""


def _token(key: str, default: str, group: str, description: str) -> Token:
    return Token(key=key, default=default, group=group, description=description)


#: The groups a token can belong to, in presentation order. A settings UI can
#: build itself from this, and the reference documentation is generated from it.
TOKEN_GROUPS: Tuple[str, ...] = (
    "surfaces",
    "text",
    "accent",
    "buttons",
    "borders",
    "inputs",
    "scroll",
    "menu",
    "status",
)


#: The tokens every Gesso stylesheet may rely on.
#:
#: The defaults are a neutral dark palette: a theme that sets nothing at all
#: still renders a coherent interface, which is why a partial theme is a
#: legitimate theme rather than an error.
BASE_TOKENS: Tuple[Token, ...] = (
    # Surfaces, dark to light.
    _token("window", "#1e1e1e", "surfaces", "The application background."),
    _token("panel", "#252526", "surfaces", "Panels that sit on the background."),
    _token("card", "#2d2d30", "surfaces", "Raised cards inside a panel."),
    _token("card_hover", "#37373d", "surfaces", "A card under the pointer."),
    _token("preview_bg", "#1a1a1a", "surfaces", "Behind a preview image."),
    _token("menu_bg", "#2d2d30", "surfaces", "Menus and message boxes."),
    _token("nav_active_bg", "#37373d", "surfaces", "The selected navigation item."),
    _token("tooltip_bg", "#3a3a3a", "surfaces", "Tooltip background."),
    _token("input_bg", "#2a2a2b", "inputs", "Text and number fields."),
    _token("status_bg", "#252526", "status", "The status bar."),
    # Text, strong to muted.
    _token("text_strong", "#f5f5f5", "text", "Headings and selected labels."),
    _token("text", "#d4d4d4", "text", "Body text."),
    _token("text_muted", "#9a9a9a", "text", "Descriptions and secondary detail."),
    _token("text_disabled", "#6b6b6b", "text", "Disabled text."),
    _token("status_text", "#c0c0c0", "status", "Status bar text."),
    _token("tooltip_text", "#f0f0f0", "text", "Tooltip text."),
    # Accent.
    _token("accent", "#7c6cf6", "accent", "The one colour that carries emphasis."),
    _token("accent_hover", "#6658d8", "accent", "Accent under the pointer."),
    _token("accent_text", "#ffffff", "accent", "Text on top of the accent."),
    # Buttons.
    _token("btn_bg", "#333333", "buttons", "Default button background."),
    _token("btn_hover", "#3f3f3f", "buttons", "Button under the pointer."),
    _token("btn_active", "#2a2a2a", "buttons", "Button while pressed."),
    # Borders.
    _token("border", "#3c3c3c", "borders", "The usual hairline."),
    _token("border_strong", "#4a4a4a", "borders", "Around interactive controls."),
    _token("input_border", "#4a4a4a", "inputs", "Around text fields."),
    _token("focus_border", "#7c6cf6", "inputs", "The focused control's outline."),
    # Selection, scrolling, menus.
    _token("selection", "#3a3356", "accent", "Selected text background."),
    _token("scroll_handle", "#4a4a4a", "scroll", "The scrollbar thumb."),
    _token("scroll_handle_hover", "#5a5a5a", "scroll", "The thumb under the pointer."),
    _token("menu_hover", "#3f3f46", "menu", "A menu entry under the pointer."),
)


class TokenContract:
    """The set of tokens a theme may set, and the rules for a missing one."""

    def __init__(self, tokens: Sequence[Token]) -> None:
        seen = set()
        for token in tokens:
            if token.key in seen:
                raise ValueError(f"duplicate token {token.key!r} in the contract")
            seen.add(token.key)
        self._tokens: Tuple[Token, ...] = tuple(tokens)
        self._by_key: Dict[str, Token] = {token.key: token for token in tokens}

    def __len__(self) -> int:
        return len(self._tokens)

    def __iter__(self):
        return iter(self._tokens)

    def __contains__(self, key: object) -> bool:
        return key in self._by_key

    @property
    def tokens(self) -> Tuple[Token, ...]:
        return self._tokens

    def token(self, key: str) -> Optional[Token]:
        return self._by_key.get(key)

    def keys(self) -> Tuple[str, ...]:
        return tuple(self._by_key)

    def defaults(self) -> Dict[str, str]:
        """The neutral palette a theme is merged onto."""
        return {token.key: token.default for token in self._tokens}

    def groups(self) -> Dict[str, List[Token]]:
        """Tokens by group, in :data:`TOKEN_GROUPS` order."""
        grouped: Dict[str, List[Token]] = {}
        for token in self._tokens:
            grouped.setdefault(token.group, []).append(token)
        ordered = {name: grouped[name] for name in TOKEN_GROUPS if name in grouped}
        # Anything with an unrecognised group still shows up, at the end.
        for name, tokens in grouped.items():
            ordered.setdefault(name, tokens)
        return ordered

    def unknown(self, colors: Mapping[str, Any]) -> List[str]:
        """Keys in *colors* the contract does not know about.

        Almost always a typo, and worth reporting: ``"acccent"`` in a theme file
        would otherwise be ignored and the accent would silently stay default.
        """
        return sorted(str(key) for key in colors if key not in self._by_key)

    def missing(self, colors: Mapping[str, Any]) -> List[str]:
        """Contract tokens absent from *colors*."""
        return sorted(key for key in self._by_key if key not in colors)

    def resolve(self, *layers: Mapping[str, Any]) -> Dict[str, str]:
        """Merge *layers* over the defaults, later layers winning.

        Values are stringified, because a palette is ultimately text
        substituted into a stylesheet.
        """
        resolved = self.defaults()
        for layer in layers:
            if not layer:
                continue
            resolved.update({str(key): str(value) for key, value in layer.items()})
        return resolved


#: The contract every Gesso application shares.
BASE_CONTRACT = TokenContract(BASE_TOKENS)
