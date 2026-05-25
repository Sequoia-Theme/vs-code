#!/usr/bin/env python3
"""Generate Sublime Text, Logseq, Base16, Shiki, and Starlight ports for Sequoia."""

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
hex6 = _gp.hex6
hex_to_hsl = _gp.hex_to_hsl
load_tokens = _gp.load_tokens
write = _gp.write
write_port = _gp.write_port
with_alpha = _gp.with_alpha

STARLIGHT_PAIRS: dict[str, tuple[str, str]] = {
    "moonlight-dark": ("moonlight-dark", "moonlight-light"),
    "moonlight-light": ("moonlight-dark", "moonlight-light"),
    "monochrome-dark": ("monochrome-dark", "monochrome-light"),
    "monochrome-light": ("monochrome-dark", "monochrome-light"),
    "retro-dark": ("retro-dark", "retro-light"),
    "retro-light": ("retro-dark", "retro-light"),
}


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


def hsl_offset(color: str, l_offset: int) -> str:
    hue, sat, light = hex_to_hsl(color)
    l_num = int(light.rstrip("%"))
    new_l = min(max(l_num + l_offset, 0), 100)
    return f"hsl({hue}, {sat}, {new_l}%)"


def starlight_mode_vars(tokens: Tokens) -> str:
    is_dark = tokens.appearance == "dark"
    accent = tokens.accent or tokens.function
    lo = -45 if is_dark else -25
    hi = 25 if is_dark else 45
    lines = [
        f"  --sl-color-accent-low: {hsl_offset(accent, lo)};",
        f"  --sl-color-accent: {hex6(accent)};",
        f"  --sl-color-accent-high: {hsl_offset(accent, hi)};",
    ]
    if is_dark:
        lines.extend(
            [
                f"  --sl-color-white: {tokens.foreground};",
                f"  --sl-color-gray-1: {hsl_offset(tokens.foreground, 8)};",
                f"  --sl-color-gray-2: {tokens.muted};",
                f"  --sl-color-gray-3: {tokens.comment};",
                f"  --sl-color-gray-4: {hsl_offset(tokens.muted, -15)};",
                f"  --sl-color-gray-5: {tokens.surface};",
                f"  --sl-color-gray-6: {hsl_offset(tokens.background, 8)};",
                f"  --sl-color-black: {tokens.background};",
            ]
        )
    else:
        lines.extend(
            [
                f"  --sl-color-white: {tokens.foreground};",
                f"  --sl-color-gray-1: {hsl_offset(tokens.foreground, 10)};",
                f"  --sl-color-gray-2: {tokens.muted};",
                f"  --sl-color-gray-3: {tokens.comment};",
                f"  --sl-color-gray-4: {hsl_offset(tokens.muted, 15)};",
                f"  --sl-color-gray-5: {hsl_offset(tokens.muted, 35)};",
                f"  --sl-color-gray-6: {hsl_offset(tokens.surface, 10)};",
                f"  --sl-color-gray-7: {tokens.surface};",
                f"  --sl-color-black: {tokens.background};",
            ]
        )

    t = tokens.terminal
    for hue_name, term_key in [
        ("orange", "yellow"),
        ("green", "green"),
        ("blue", "cyan"),
        ("purple", "magenta"),
        ("red", "red"),
    ]:
        color = t[term_key]
        hue, _, _ = hex_to_hsl(color)
        lines.append(f"  --sl-hue-{hue_name}: {hue};")
        lines.append(
            f"  --sl-color-{hue_name}-low: {hsl_offset(color, -30 if is_dark else 30)};"
        )
        lines.append(f"  --sl-color-{hue_name}: {hex6(color)};")
        lines.append(
            f"  --sl-color-{hue_name}-high: {hsl_offset(color, 15 if is_dark else -15)};"
        )
    return "\n".join(lines)


def starlight_css(
    dark: Tokens, light: Tokens, *, brand: str, variant_label: str
) -> str:
    layer = brand.lower()
    return f"""/* {brand} {variant_label} for Astro Starlight */
@layer starlight, {layer};

@layer {layer} {{
  :root,
  ::backdrop {{
{starlight_mode_vars(dark)}
  }}

  :root[data-theme='light'],
  [data-theme='light'] ::backdrop {{
{starlight_mode_vars(light)}
  }}
}}
"""


def astro_config_example(*, brand: str, css_file: str, dark_json: str, light_json: str) -> str:
    return f"""// Example astro.config.mjs — {brand} for Starlight
import {{ defineConfig }} from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({{
  integrations: [
    starlight({{
      title: 'My Docs',
      customCss: ['./src/styles/{css_file}'],
      expressiveCode: {{
        themes: [
          './src/themes/{dark_json}',
          './src/themes/{light_json}',
        ],
      }},
    }}),
  ],
}});
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

    starlight_files: list[str] = []
    for vid in all_tokens:
        dark_id, light_id = STARLIGHT_PAIRS[vid]
        dark_tok = all_tokens[dark_id]
        light_tok = all_tokens[light_id]
        css_name = f"{PREFIX}-{vid}.css"
        starlight_files.append(css_name)
        write(
            OUT / "starlight" / css_name,
            starlight_css(
                dark_tok,
                light_tok,
                brand="Sequoia",
                variant_label=dark_tok.name.replace("Sequoia ", ""),
            ),
        )
        for pair_id in {dark_id, light_id}:
            json_name = f"{PREFIX}-{pair_id}.json"
            if json_name not in starlight_files:
                starlight_files.append(json_name)
                fname = dict(VARIANTS)[pair_id]
                write(OUT / "starlight" / json_name, shiki_theme(pair_id, fname))
    example_name = "astro.config.example.mjs"
    starlight_files.append(example_name)
    write(
        OUT / "starlight" / example_name,
        astro_config_example(
            brand="Sequoia Moonlight",
            css_file=f"{PREFIX}-moonlight-dark.css",
            dark_json=f"{PREFIX}-moonlight-dark.json",
            light_json=f"{PREFIX}-moonlight-light.json",
        ),
    )
    write_port(
        "starlight",
        "Copy a `.css` file and matching Shiki `.json` themes into your Starlight project. "
        "Add the CSS path to `starlight({ customCss })` and JSON paths to `expressiveCode.themes`. "
        "See `astro.config.example.mjs`.",
        "Sequoia for Starlight",
        starlight_files,
    )

    print("Generated extra Sequoia ports in", OUT)


if __name__ == "__main__":
    generate()
