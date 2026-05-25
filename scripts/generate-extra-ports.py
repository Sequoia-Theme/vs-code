#!/usr/bin/env python3
"""Generate Sublime Text, Logseq, Base16, and Shiki ports for Sequoia."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "generate_ports", ROOT / "scripts" / "generate-ports.py"
)
_gp = importlib.util.module_from_spec(_spec)
sys.modules["generate_ports"] = _gp
assert _spec.loader is not None
_spec.loader.exec_module(_gp)

OUT = _gp.OUT
THEMES = _gp.THEMES
PREFIX = _gp.PREFIX
VARIANTS = _gp.VARIANTS
Tokens = _gp.Tokens
bat_tmtheme = _gp.bat_tmtheme
load_tokens = _gp.load_tokens
write = _gp.write
write_port = _gp.write_port
with_alpha = _gp.with_alpha


def logseq_css_vars(tokens: Tokens) -> str:
    return f"""  --ls-primary-background-color: {tokens.background};
  --ls-primary-text-color: {tokens.foreground};
  --ls-secondary-background-color: {tokens.surface};
  --ls-secondary-text-color: {tokens.muted};
  --ls-link-text-color: {tokens.function};
  --ls-link-text-hover-color: {tokens.accent};
  --ls-border-color: {with_alpha(tokens.muted, "40")};
  --ls-icon-color: {tokens.muted};
  --ls-selection-background-color: {tokens.selection_bg};
  --ls-block-bullet-color: {tokens.accent};
  --ls-page-checkbox-color: {tokens.accent};
  --ls-focus-ring-color: {with_alpha(tokens.accent, "77")};
  --ls-code-block-background-color: {tokens.surface};
  --ls-page-title-color: {tokens.foreground};
  --ls-h2-color: {tokens.type_color};
  --ls-h3-color: {tokens.keyword};
  --ct-background: {tokens.background};
  --ct-page-font-color: {tokens.foreground};
"""


def logseq_css(tokens: Tokens, *, brand: str) -> str:
    return f"""/* {brand} {tokens.name} for Logseq */
:root {{
{logseq_css_vars(tokens)}
}}
"""


def base16_yaml(tokens: Tokens, *, brand: str) -> str:
    t = tokens.terminal
    return f"""system: "base16"
name: "{tokens.name}"
author: "Micheal Andreuzza (https://michaelandreuzza.com/)"
description: "{brand} {tokens.name} from the {brand} theme family"
variant: "{tokens.appearance}"
palette:
  base00: "{tokens.background}"
  base01: "{tokens.surface}"
  base02: "{tokens.surface}"
  base03: "{tokens.comment}"
  base04: "{tokens.muted}"
  base05: "{tokens.foreground}"
  base06: "{tokens.foreground}"
  base07: "{tokens.accent_fg}"
  base08: "{t['red']}"
  base09: "{tokens.function}"
  base0A: "{t['yellow']}"
  base0B: "{t['green']}"
  base0C: "{t['cyan']}"
  base0D: "{tokens.type_color}"
  base0E: "{tokens.string}"
  base0F: "{tokens.constant}"
"""


def shiki_theme(vid: str, fname: str) -> str:
    raw = json.loads((THEMES / fname).read_text(encoding="utf-8"))
    return json.dumps(
        {
            "name": raw.get("name"),
            "type": raw.get("type", "dark"),
            "colors": raw.get("colors", {}),
            "tokenColors": raw.get("tokenColors", []),
        },
        indent=2,
    ) + "\n"


def generate() -> None:
    all_tokens = {vid: load_tokens(vid, fname) for vid, fname in VARIANTS}

    sublime_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.tmTheme"
        sublime_files.append(f)
        write(OUT / "sublime-text" / f, bat_tmtheme(tok))
    write_port(
        "sublime-text",
        "Copy `.tmTheme` files to Sublime `Packages/User/` and pick **Preferences → Color Scheme**.",
        "Sequoia for Sublime Text",
        sublime_files,
    )

    logseq_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.css"
        logseq_files.append(f)
        write(OUT / "logseq" / f, logseq_css(tok, brand="Sequoia"))
    write(
        OUT / "logseq" / "MARKETPLACE.md",
        "# Publish Sequoia to Logseq Marketplace\n\nSee Serendipity-Theme/logseq MARKETPLACE.md for steps.\n",
    )
    logseq_files.append("MARKETPLACE.md")
    write_port(
        "logseq",
        "Import CSS into Logseq **Settings → Custom CSS**.",
        "Sequoia for Logseq",
        logseq_files,
    )

    base16_files: list[str] = []
    for vid, tok in all_tokens.items():
        f = f"{PREFIX}-{vid}.yaml"
        base16_files.append(f)
        write(OUT / "base16" / f, base16_yaml(tok, brand="Sequoia"))
    write_port(
        "base16",
        "Submit YAML files to [tinted-theming/schemes](https://github.com/tinted-theming/schemes).",
        "Sequoia for Base16",
        base16_files,
    )

    shiki_files: list[str] = []
    for vid, fname in VARIANTS:
        f = f"{PREFIX}-{vid}.json"
        shiki_files.append(f)
        write(OUT / "shiki" / f, shiki_theme(vid, fname))
    write_port(
        "shiki",
        "Import JSON themes into [Shiki](https://shiki.style/).",
        "Sequoia for Shiki",
        shiki_files,
    )

    print("Generated extra Sequoia ports in", OUT)


if __name__ == "__main__":
    generate()
