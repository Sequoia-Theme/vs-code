#!/usr/bin/env python3
"""Generate Sequoia theme ports from VS Code theme JSON files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"
OUT = ROOT.parent / "sequoia-ports"
PALETTE_OUT = ROOT.parent / "sequoia-color-palette"
TEMPLATE_OUT = ROOT.parent / "sequoia-template-for-repositories"

VARIANTS = [
    ("moonlight-dark", "sequoia-moonlight.json"),
    ("moonlight-light", "sequoia-moonlight-light.json"),
    ("monochrome-dark", "sequoia-monochrome.json"),
    ("monochrome-light", "sequoia-monochrome-light.json"),
    ("retro-dark", "sequoia-retro.json"),
    ("retro-light", "sequoia-retro-light.json"),
]

LICENSE = """MIT License

Copyright (c) Micheal Andreuzza

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

HEADER = "https://raw.githubusercontent.com/Sequoia-Theme/assets/main/githubHeader.png"
WEBSITE = "https://www.michaelandreuzza.com/vscode/sequoia/"


@dataclass
class Tokens:
    variant_id: str
    name: str
    appearance: str
    background: str
    foreground: str
    surface: str
    cursor: str
    selection_bg: str
    comment: str
    accent: str
    accent_fg: str
    muted: str
    keyword: str
    string: str
    variable: str
    function: str
    type_color: str
    constant: str
    operator: str
    error: str
    terminal: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "appearance": self.appearance,
            "background": self.background,
            "foreground": self.foreground,
            "surface": self.surface,
            "cursor": self.cursor,
            "selection_bg": self.selection_bg,
            "comment": self.comment,
            "accent": self.accent,
            "accent_fg": self.accent_fg,
            "muted": self.muted,
            "syntax": {
                "keyword": self.keyword,
                "string": self.string,
                "variable": self.variable,
                "function": self.function,
                "type": self.type_color,
                "constant": self.constant,
                "operator": self.operator,
                "error": self.error,
            },
            "terminal": self.terminal,
        }


def hex6(value: str | None, fallback: str = "#000000") -> str:
    if not value:
        return fallback
    value = value.strip().lower()
    if value in ("#0000", "transparent"):
        return fallback
    if len(value) >= 7:
        return value[:7]
    return fallback


def with_alpha(color: str, alpha: str = "33") -> str:
    base = hex6(color)
    return f"{base}{alpha}"


def scope_fg(token_colors: list, *needles: str) -> str | None:
    for rule in token_colors:
        scopes = rule.get("scope")
        fg = rule.get("settings", {}).get("foreground")
        if not fg:
            continue
        if isinstance(scopes, str):
            items = [scopes]
        else:
            items = scopes or []
        for item in items:
            for needle in needles:
                if item == needle or item.startswith(needle):
                    return fg
    return None


def load_tokens(variant_id: str, filename: str) -> Tokens:
    data = json.loads((THEMES / filename).read_text(encoding="utf-8"))
    colors = data["colors"]
    token_colors = data.get("tokenColors", [])

    bg = hex6(colors.get("editor.background"))
    fg = hex6(colors.get("editor.foreground"))
    surface = hex6(
        colors.get("banner.background")
        or colors.get("sideBar.background")
        or colors.get("activityBar.background")
        or bg
    )

    terminal = {
        "black": hex6(colors.get("terminal.ansiBlack")),
        "red": hex6(colors.get("terminal.ansiRed")),
        "green": hex6(colors.get("terminal.ansiGreen")),
        "yellow": hex6(colors.get("terminal.ansiYellow")),
        "blue": hex6(colors.get("terminal.ansiBlue")),
        "magenta": hex6(colors.get("terminal.ansiMagenta")),
        "cyan": hex6(colors.get("terminal.ansiCyan")),
        "white": hex6(colors.get("terminal.ansiWhite")),
        "bright_black": hex6(colors.get("terminal.ansiBrightBlack")),
        "bright_red": hex6(colors.get("terminal.ansiBrightRed")),
        "bright_green": hex6(colors.get("terminal.ansiBrightGreen")),
        "bright_yellow": hex6(colors.get("terminal.ansiBrightYellow")),
        "bright_blue": hex6(colors.get("terminal.ansiBrightBlue")),
        "bright_magenta": hex6(colors.get("terminal.ansiBrightMagenta")),
        "bright_cyan": hex6(colors.get("terminal.ansiBrightCyan")),
        "bright_white": hex6(colors.get("terminal.ansiBrightWhite")),
    }

    return Tokens(
        variant_id=variant_id,
        name=data["name"],
        appearance=data.get("type", "dark"),
        background=bg,
        foreground=fg,
        surface=surface,
        cursor=hex6(colors.get("editorCursor.foreground"), fg),
        selection_bg=colors.get("editor.selectionBackground", with_alpha(fg)),
        comment=hex6(scope_fg(token_colors, "comment") or colors.get("descriptionForeground")),
        accent=hex6(colors.get("button.background")),
        accent_fg=hex6(colors.get("button.foreground"), bg),
        muted=hex6(colors.get("descriptionForeground")),
        keyword=hex6(scope_fg(token_colors, "keyword", "storage.type"), fg),
        string=hex6(scope_fg(token_colors, "string"), fg),
        variable=hex6(scope_fg(token_colors, "variable"), fg),
        function=hex6(scope_fg(token_colors, "support.function"), fg),
        type_color=hex6(
            scope_fg(token_colors, "entity.name.type", "entity.name.tag", "entity.name.section"),
            fg,
        ),
        constant=hex6(scope_fg(token_colors, "constant"), fg),
        operator=hex6(scope_fg(token_colors, "punctuation"), colors.get("descriptionForeground", fg)),
        error=hex6(colors.get("errorForeground") or scope_fg(token_colors, "invalid"), fg),
        terminal=terminal,
    )


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def variant_label(variant_id: str) -> str:
    family, mode = variant_id.rsplit("-", 1)
    return f"{family.title()} {mode.title()}"


def port_readme(title: str, install: str, files: list[str]) -> str:
    variants = "\n".join(f"- **{variant_label(vid)}** — {mode}" for vid, mode in [
        ("moonlight-dark", "dark"), ("moonlight-light", "light"),
        ("monochrome-dark", "dark"), ("monochrome-light", "light"),
        ("retro-dark", "dark"), ("retro-light", "light"),
    ])
    file_list = ", ".join(f"`{name}`" for name in files)
    return f"""![Sequoia]({HEADER})

# {title}

Black, elegant, modern, monochrome or colourful theme for your tools.

See other interfaces at the [official website]({WEBSITE}).

## Available themes

{variants}

## Installation

{install}

Available files: {file_list}.

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
"""


def ghostty(tokens: Tokens) -> str:
    t = tokens.terminal
    lines = [
        f"background = {tokens.background}",
        f"foreground = {tokens.foreground}",
        f"cursor-color = {tokens.cursor}",
        f"cursor-text = {tokens.background}",
        f"selection-background = {tokens.selection_bg}",
        f"selection-foreground = {tokens.foreground}",
    ]
    order = [
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
        "bright_black", "bright_red", "bright_green", "bright_yellow",
        "bright_blue", "bright_magenta", "bright_cyan", "bright_white",
    ]
    for idx, key in enumerate(order):
        lines.append(f"palette = {idx}={t[key]}")
    return "\n".join(lines) + "\n"


def starship(tokens: Tokens) -> str:
    palette = tokens.variant_id.replace("-", "_")
    return f"""# Sequoia {tokens.name}
palette = "{palette}"

[palettes.{palette}]
background = "{tokens.background}"
current_line = "{tokens.surface}"
foreground = "{tokens.foreground}"
comment = "{tokens.comment}"
cyan = "{tokens.function}"
green = "{tokens.type_color}"
orange = "{tokens.variable}"
pink = "{tokens.variable}"
purple = "{tokens.string}"
red = "{tokens.error}"
yellow = "{tokens.constant}"

[character]
success_symbol = "[✔]({tokens.keyword})"
error_symbol = "[✘]({tokens.error})"

[directory]
style = "bold {tokens.type_color}"

[git_branch]
style = "bold {tokens.function}"

[git_status]
style = "bold {tokens.variable}"
"""


def lazygit(tokens: Tokens) -> str:
    return f"""# Sequoia {tokens.name}
theme:
  activeBorderColor:
    - "{tokens.accent}"
    - bold
  inactiveBorderColor:
    - "{tokens.type_color}"
  searchingActiveBorderColor:
    - "{tokens.function}"
    - bold
  optionsTextColor:
    - "{tokens.muted}"
  selectedLineBgColor:
    - "{tokens.selection_bg}"
  cherryPickedCommitFgColor:
    - "{tokens.muted}"
  cherryPickedCommitBgColor:
    - "{tokens.function}"
  markedBaseCommitFgColor:
    - "{tokens.function}"
  markedBaseCommitBgColor:
    - "{tokens.type_color}"
  unstagedChangesColor:
    - "{tokens.muted}"
  defaultFgColor:
    - "{tokens.foreground}"
"""


def neovim(tokens: Tokens) -> str:
    bg = tokens.background
    return f"""-- Sequoia {tokens.name} for Neovim
vim.cmd('hi clear')
if vim.fn.exists('syntax_on') then
  vim.cmd('syntax reset')
end
vim.o.background = '{tokens.appearance}'
vim.g.colors_name = 'sequoia-{tokens.variant_id}'

local M = {{}}
function M.setup()
  vim.cmd('hi Normal guifg={tokens.foreground} guibg={bg}')
  vim.cmd('hi Cursor guifg={tokens.cursor} guibg={bg}')
  vim.cmd('hi Visual guifg={tokens.foreground} guibg={tokens.selection_bg}')
  vim.cmd('hi LineNr guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi CursorLineNr guifg={tokens.foreground} guibg={bg} gui=bold')
  vim.cmd('hi CursorLine guibg={with_alpha(tokens.muted, "1a")}')
  vim.cmd('hi Comment guifg={tokens.comment} gui=italic')
  vim.cmd('hi Constant guifg={tokens.constant}')
  vim.cmd('hi String guifg={tokens.string}')
  vim.cmd('hi Character guifg={tokens.string}')
  vim.cmd('hi Number guifg={tokens.constant}')
  vim.cmd('hi Boolean guifg={tokens.constant}')
  vim.cmd('hi Float guifg={tokens.constant}')
  vim.cmd('hi Identifier guifg={tokens.variable} gui=italic')
  vim.cmd('hi Function guifg={tokens.function} gui=italic')
  vim.cmd('hi Statement guifg={tokens.keyword}')
  vim.cmd('hi Conditional guifg={tokens.keyword}')
  vim.cmd('hi Repeat guifg={tokens.keyword}')
  vim.cmd('hi Keyword guifg={tokens.keyword}')
  vim.cmd('hi Label guifg={tokens.keyword}')
  vim.cmd('hi Operator guifg={tokens.operator}')
  vim.cmd('hi Exception guifg={tokens.error}')
  vim.cmd('hi PreProc guifg={tokens.keyword}')
  vim.cmd('hi Type guifg={tokens.type_color}')
  vim.cmd('hi StorageClass guifg={tokens.keyword}')
  vim.cmd('hi Structure guifg={tokens.type_color}')
  vim.cmd('hi Typedef guifg={tokens.type_color}')
  vim.cmd('hi Special guifg={tokens.type_color}')
  vim.cmd('hi SpecialChar guifg={tokens.string}')
  vim.cmd('hi Tag guifg={tokens.type_color}')
  vim.cmd('hi Delimiter guifg={tokens.operator}')
  vim.cmd('hi SpecialComment guifg={tokens.comment} gui=italic')
  vim.cmd('hi Underlined guifg={tokens.function} gui=underline')
  vim.cmd('hi Error guifg={tokens.error}')
  vim.cmd('hi Todo guifg={tokens.variable} gui=bold')
  vim.cmd('hi StatusLine guifg={tokens.foreground} guibg={tokens.surface}')
  vim.cmd('hi StatusLineNC guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi TabLine guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi TabLineFill guifg={tokens.surface} guibg={bg}')
  vim.cmd('hi TabLineSel guifg={tokens.foreground} guibg={bg} gui=bold')
  vim.cmd('hi WinSeparator guifg={tokens.muted} guibg={bg}')
  vim.cmd('hi Pmenu guifg={tokens.foreground} guibg={tokens.surface}')
  vim.cmd('hi PmenuSel guifg={tokens.foreground} guibg={tokens.selection_bg}')
  vim.cmd('hi Search guifg={tokens.foreground} guibg={tokens.selection_bg}')
  vim.cmd('hi IncSearch guifg={bg} guibg={tokens.accent} gui=bold')
  vim.cmd('hi DiffAdd guifg={tokens.type_color} guibg={bg}')
  vim.cmd('hi DiffChange guifg={tokens.variable} guibg={bg}')
  vim.cmd('hi DiffDelete guifg={tokens.error} guibg={bg}')
  vim.cmd('hi DiffText guifg={tokens.function} guibg={bg}')
  vim.cmd('hi @variable guifg={tokens.variable} gui=italic')
  vim.cmd('hi @variable.parameter guifg={tokens.function}')
  vim.cmd('hi @function guifg={tokens.function} gui=italic')
  vim.cmd('hi @function.builtin guifg={tokens.function} gui=italic')
  vim.cmd('hi @keyword guifg={tokens.keyword}')
  vim.cmd('hi @type guifg={tokens.type_color}')
  vim.cmd('hi @string guifg={tokens.string}')
  vim.cmd('hi @comment guifg={tokens.comment} gui=italic')
  vim.cmd('hi @tag guifg={tokens.type_color}')
  vim.cmd('hi @tag.attribute guifg={tokens.function} gui=italic')
end

M.setup()
return M
"""


def zed_family(family_name: str, dark: Tokens, light: Tokens) -> dict:
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": family_name,
        "author": "Micheal Andreuzza",
        "themes": [
            zed_theme_variant(dark),
            zed_theme_variant(light),
        ],
    }


def zed_theme(tokens: Tokens) -> dict:
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": tokens.name,
        "author": "Micheal Andreuzza",
        "themes": [zed_theme_variant(tokens)],
    }


def zed_theme_variant(tokens: Tokens) -> dict:
    t = tokens.terminal
    ff = lambda c: f"{c}ff" if len(c) == 7 else c
    border = with_alpha(tokens.muted, "33")
    return {
            "name": tokens.name,
            "appearance": tokens.appearance,
            "style": {
                "accents": [
                    ff(tokens.type_color), ff(tokens.variable), ff(tokens.function),
                    ff(tokens.keyword), ff(tokens.string), ff(tokens.error), ff(tokens.muted),
                ],
                "background": ff(tokens.background),
                "border": border,
                "border.focused": with_alpha(tokens.accent, "77"),
                "border.selected": with_alpha(tokens.accent, "bb"),
                "border.transparent": "#00000000",
                "elevated_surface.background": ff(tokens.surface),
                "surface.background": ff(tokens.background) + "ee",
                "element.background": ff(tokens.surface),
                "element.hover": ff(tokens.muted),
                "element.selected": ff(tokens.muted),
                "text": ff(tokens.foreground),
                "text.muted": ff(tokens.muted),
                "text.accent": ff(tokens.accent),
                "icon": ff(tokens.foreground),
                "icon.muted": ff(tokens.muted),
                "status_bar.background": ff(tokens.background),
                "title_bar.background": ff(tokens.background),
                "toolbar.background": ff(tokens.surface),
                "tab_bar.background": ff(tokens.background),
                "tab.inactive_background": ff(tokens.background),
                "tab.active_background": ff(tokens.background),
                "panel.background": ff(tokens.background),
                "editor.foreground": ff(tokens.foreground),
                "editor.background": ff(tokens.background),
                "editor.gutter.background": ff(tokens.background),
                "editor.active_line.background": border,
                "editor.line_number": ff(tokens.muted),
                "editor.active_line_number": ff(tokens.foreground),
                "scrollbar.thumb.background": with_alpha(tokens.muted, "77"),
                "scrollbar.track.background": ff(tokens.background),
                "terminal.background": ff(tokens.background),
                "terminal.foreground": ff(tokens.foreground),
                "terminal.ansi.black": ff(t["black"]),
                "terminal.ansi.red": ff(t["red"]),
                "terminal.ansi.green": ff(t["green"]),
                "terminal.ansi.yellow": ff(t["yellow"]),
                "terminal.ansi.blue": ff(t["blue"]),
                "terminal.ansi.magenta": ff(t["magenta"]),
                "terminal.ansi.cyan": ff(t["cyan"]),
                "terminal.ansi.white": ff(t["white"]),
                "terminal.ansi.bright_black": ff(t["bright_black"]),
                "terminal.ansi.bright_red": ff(t["bright_red"]),
                "terminal.ansi.bright_green": ff(t["bright_green"]),
                "terminal.ansi.bright_yellow": ff(t["bright_yellow"]),
                "terminal.ansi.bright_blue": ff(t["bright_blue"]),
                "terminal.ansi.bright_magenta": ff(t["bright_magenta"]),
                "terminal.ansi.bright_cyan": ff(t["bright_cyan"]),
                "terminal.ansi.bright_white": ff(t["bright_white"]),
                "syntax": {
                    "comment": {"color": ff(tokens.comment), "font_style": "italic"},
                    "keyword": {"color": ff(tokens.keyword)},
                    "string": {"color": ff(tokens.string)},
                    "function": {"color": ff(tokens.function), "font_style": "italic"},
                    "variable": {"color": ff(tokens.variable), "font_style": "italic"},
                    "type": {"color": ff(tokens.type_color)},
                    "constant": {"color": ff(tokens.constant)},
                    "tag": {"color": ff(tokens.type_color)},
                    "attribute": {"color": ff(tokens.function), "font_style": "italic"},
                    "punctuation": {"color": ff(tokens.operator)},
                },
            },
    }


def obsidian_css(tokens: Tokens) -> str:
    selector = ".theme-dark" if tokens.appearance == "dark" else ".theme-light"
    return f"""/* Sequoia {tokens.name} for Obsidian */
{selector} {{
  --background-primary: {tokens.background};
  --background-primary-alt: {tokens.background};
  --background-secondary: {tokens.surface};
  --background-secondary-alt: {tokens.background};
  --text-normal: {tokens.foreground};
  --text-muted: {tokens.muted};
  --text-faint: {tokens.muted};
  --text-accent: {tokens.accent};
  --text-accent-hover: {tokens.function};
  --text-on-accent: {tokens.accent_fg};
  --interactive-accent: {tokens.accent};
  --interactive-accent-hover: {tokens.function};
  --text-selection: {tokens.selection_bg};
  --text-link: {tokens.function};
  --text-a: {tokens.function};
  --text-a-hover: {tokens.keyword};
  --text-mark: {tokens.type_color};
  --text-tag: {tokens.string};
  --markup-code: {tokens.string};
  --code-normal: {tokens.string};
  --code-comment: {tokens.comment};
  --code-function: {tokens.function};
  --code-keyword: {tokens.keyword};
  --code-important: {tokens.error};
  --code-property: {tokens.type_color};
  --code-punctuation: {tokens.operator};
  --code-string: {tokens.string};
  --code-tag: {tokens.type_color};
  --code-value: {tokens.constant};
  --blockquote-border: {tokens.function};
  --titlebar-background: {tokens.background};
  --titlebar-background-focused: {tokens.background};
  --tab-background-active: {tokens.background};
  --tab-text-color-focused-active: {tokens.foreground};
  --nav-item-background-hover: {tokens.selection_bg};
  --nav-item-background-active: {tokens.selection_bg};
  --checkbox-color: {tokens.accent};
  --checkbox-color-hover: {tokens.function};
}}
"""


def prism_css(tokens: Tokens) -> str:
    return f"""/* Sequoia {tokens.name} for Prism.js */
code[class*="language-"],
pre[class*="language-"] {{
  color: {tokens.foreground};
  background: {tokens.background};
}}
.token.comment, .token.prolog, .token.doctype, .token.cdata {{
  color: {tokens.comment};
  font-style: italic;
}}
.token.keyword, .token.atrule, .token.tag, .token.selector {{
  color: {tokens.keyword};
}}
.token.string, .token.char, .token.attr-value {{
  color: {tokens.string};
}}
.token.function, .token.class-name {{
  color: {tokens.function};
  font-style: italic;
}}
.token.number, .token.boolean, .token.constant {{
  color: {tokens.constant};
}}
.token.operator, .token.punctuation {{
  color: {tokens.operator};
}}
.token.variable {{
  color: {tokens.variable};
  font-style: italic;
}}
.token.property, .token.builtin {{
  color: {tokens.type_color};
}}
.token.deleted {{
  color: {tokens.error};
}}
"""


def shadcn_globals(tokens: Tokens) -> str:
    return f"""/* Sequoia {tokens.name} — shadcn/ui CSS variables */
@layer base {{
  :root {{
    --background: {tokens.background};
    --foreground: {tokens.foreground};
    --card: {tokens.background};
    --card-foreground: {tokens.foreground};
    --popover: {tokens.surface};
    --popover-foreground: {tokens.foreground};
    --primary: {tokens.accent};
    --primary-foreground: {tokens.accent_fg};
    --secondary: {tokens.surface};
    --secondary-foreground: {tokens.foreground};
    --muted: {tokens.background};
    --muted-foreground: {tokens.muted};
    --accent: {tokens.function};
    --accent-foreground: {tokens.foreground};
    --destructive: {tokens.error};
    --destructive-foreground: {tokens.foreground};
    --border: {with_alpha(tokens.muted, "33")};
    --input: {with_alpha(tokens.muted, "33")};
    --ring: {tokens.accent};
    --chart-1: {tokens.keyword};
    --chart-2: {tokens.type_color};
    --chart-3: {tokens.string};
    --chart-4: {tokens.constant};
    --chart-5: {tokens.error};
    --radius: 0.5rem;
  }}
}}
"""


def generate_all(all_tokens: dict[str, Tokens]) -> None:
    if OUT.exists():
        import shutil
        shutil.rmtree(OUT)
    OUT.mkdir()

    ghostty_files = []
    for vid, tok in all_tokens.items():
        name = f"sequoia-{vid}"
        ghostty_files.append(name)
        write(OUT / "ghostty" / name, ghostty(tok))

    write(OUT / "ghostty" / "LICENSE", LICENSE + "\n")
    write(OUT / "ghostty" / "README.md", port_readme(
        "Sequoia for Ghostty",
        """1. Clone or download this repository.
2. Copy the variant you want into your Ghostty config directory, or add an include to `~/.config/ghostty/config`:

```
config-file = ~/.config/ghostty/sequoia-moonlight-dark
```

3. Restart Ghostty.""",
        ghostty_files,
    ))

    starship_files = []
    for vid, tok in all_tokens.items():
        fname = f"starship-{vid}.toml"
        starship_files.append(fname)
        write(OUT / "starship" / fname, starship(tok))

    write(OUT / "starship" / "LICENSE", LICENSE + "\n")
    write(OUT / "starship" / "README.md", port_readme(
        "Sequoia for Starship",
        """1. Copy a TOML file to `~/.config/starship/` or merge into `starship.toml`.
2. Set `palette` to the variant name (e.g. `moonlight_dark`).
3. Restart your shell.""",
        starship_files,
    ))

    lazygit_files = []
    for vid, tok in all_tokens.items():
        fname = f"lazygit-{vid}.yml"
        lazygit_files.append(fname)
        write(OUT / "lazygit" / fname, lazygit(tok))

    write(OUT / "lazygit" / "LICENSE", LICENSE + "\n")
    write(OUT / "lazygit" / "README.md", port_readme(
        "Sequoia for Lazygit",
        """1. Copy a YAML file to your Lazygit config path.
2. Reference it from `~/.config/lazygit/config.yml` under `gui.theme` or merge the `theme` block.""",
        lazygit_files,
    ))

    neovim_files = []
    for vid, tok in all_tokens.items():
        fname = f"sequoia-{vid}.lua"
        neovim_files.append(f"colors/{fname}")
        write(OUT / "neovim" / "colors" / fname, neovim(tok))

    write(OUT / "neovim" / "LICENSE", LICENSE + "\n")
    write(OUT / "neovim" / "README.md", port_readme(
        "Sequoia for Neovim",
        """1. Copy the `colors/` folder into your Neovim config.
2. Enable with `:colorscheme sequoia-moonlight-dark` (or any variant).""",
        neovim_files,
    ))

    zed_files = []
    zed_families = [
        ("sequoia-moonlight", "Sequoia Moonlight", "moonlight-dark", "moonlight-light"),
        ("sequoia-monochrome", "Sequoia Monochrome", "monochrome-dark", "monochrome-light"),
        ("sequoia-retro", "Sequoia Retro", "retro-dark", "retro-light"),
    ]
    for slug, family_name, dark_id, light_id in zed_families:
        fname = f"{slug}.json"
        zed_files.append(f"themes/{fname}")
        family = zed_family(family_name, all_tokens[dark_id], all_tokens[light_id])
        write(OUT / "zed" / "themes" / fname, json.dumps(family, indent=2) + "\n")

    write(OUT / "zed" / "extension.toml", """id = "sequoia"
name = "Sequoia"
version = "1.1.0"
schema_version = 1
authors = ["Micheal Andreuzza <michael@andreuzza.com>"]
description = "Sequoia theme for Zed — Moonlight, Monochrome, and Retro (dark and light)"
repository = "https://github.com/Sequoia-Theme/zed"
""")
    write(OUT / "zed" / "LICENSE", LICENSE + "\n")
    write(OUT / "zed" / "README.md", port_readme(
        "Sequoia for Zed",
        """1. In Zed, run **zed: extensions** → **Install Dev Extension** and select this repo.
2. Open the theme picker (**cmd+k cmd+t** / **ctrl+k ctrl+t**).
3. Choose **Sequoia Moonlight**, **Sequoia Monochrome**, or **Sequoia Retro**, then pick **Dark** or **Light**.""",
        zed_files,
    ))

    obsidian_files = []
    for vid, tok in all_tokens.items():
        fname = f"sequoia-{vid}.css"
        obsidian_files.append(fname)
        write(OUT / "obsidian" / fname, obsidian_css(tok))

    write(OUT / "obsidian" / "LICENSE", LICENSE + "\n")
    write(OUT / "obsidian" / "README.md", port_readme(
        "Sequoia for Obsidian",
        """1. Copy a CSS file into your vault's `.obsidian/snippets/` folder.
2. Enable the snippet in **Settings → Appearance → CSS snippets**.""",
        obsidian_files,
    ))

    prism_files = []
    for vid, tok in all_tokens.items():
        fname = f"sequoia-{vid}.css"
        prism_files.append(fname)
        write(OUT / "prism" / fname, prism_css(tok))

    write(OUT / "prism" / "LICENSE", LICENSE + "\n")
    write(OUT / "prism" / "README.md", port_readme(
        "Sequoia for Prism.js",
        """1. Include the CSS file in your site.
2. Use with `prism.js` as usual.""",
        prism_files,
    ))

    shadcn_dirs = []
    preset_entries = []
    for vid, tok in all_tokens.items():
        shadcn_dirs.append(f"{vid}/globals.css")
        write(OUT / "shadcn-ui" / vid / "globals.css", shadcn_globals(tok))
        key = vid.replace("-", "_")
        preset_entries.append(f"""      "{vid}": {{
            "background": "{tok.background}",
            "foreground": "{tok.foreground}",
            "surface": "{tok.surface}",
            "accent": "{tok.accent}",
            "muted": "{tok.muted}",
            "keyword": "{tok.keyword}",
            "string": "{tok.string}",
            "error": "{tok.error}"
      }}""")

    preset_body = ",\n".join(preset_entries)
    write(OUT / "shadcn-ui" / "tailwind.preset.js", f"""/** @type {{import('tailwindcss').Config}} */
module.exports = {{
  theme: {{
    extend: {{
      colors: {{
{preset_body}
      }}
    }},
  }},
}};
""")
    write(OUT / "shadcn-ui" / "LICENSE", LICENSE + "\n")
    write(OUT / "shadcn-ui" / "README.md", port_readme(
        "Sequoia for shadcn/ui",
        """1. Copy a variant folder's `globals.css` into your app.
2. Import it in your root layout.
3. Optionally extend `tailwind.preset.js` in your Tailwind config.""",
        shadcn_dirs + ["tailwind.preset.js"],
    ))


def generate_tokens_json(all_tokens: dict[str, Tokens]) -> None:
    grouped: dict[str, dict] = {}
    for vid, tok in all_tokens.items():
        family, mode = vid.rsplit("-", 1)
        grouped.setdefault(family, {})[mode] = tok.to_dict()

    PALETTE_OUT.mkdir(parents=True, exist_ok=True)
    write(PALETTE_OUT / "tokens.json", json.dumps(grouped, indent=2) + "\n")
    write(PALETTE_OUT / "LICENSE", LICENSE + "\n")
    write(PALETTE_OUT / "README.md", f"""# Sequoia color palette

Design tokens extracted from [Sequoia VS Code](https://github.com/Sequoia-Theme/vs-code).

See the theme on the [official website]({WEBSITE}).

## tokens.json

Structured colors for **Moonlight**, **Monochrome**, and **Retro** in dark and light modes.

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
""")


def generate_template() -> None:
    TEMPLATE_OUT.mkdir(parents=True, exist_ok=True)
    write(TEMPLATE_OUT / "LICENSE", LICENSE + "\n")
    write(TEMPLATE_OUT / "README.md", f"""![Sequoia]({HEADER})

# Sequoia theme port — {{APP_NAME}}

Port of the [Sequoia](https://github.com/Sequoia-Theme/vs-code) theme for **{{APP_NAME}}**.

See other interfaces at the [official website]({WEBSITE}).

## Variants

Sequoia ships six VS Code themes:

- **Moonlight Dark** / **Moonlight Light**
- **Monochrome Dark** / **Monochrome Light**
- **Retro Dark** / **Retro Light**

Use the same naming pattern in this repo: `sequoia-{{variant}}-{{mode}}`.

## README sections

1. Installation steps for {{APP_NAME}}
2. Screenshots
3. Who ported the theme

## Created by

[Micheal Andreuzza](https://github.com/michael-andreuzza)
""")


def main() -> None:
    all_tokens = {vid: load_tokens(vid, fname) for vid, fname in VARIANTS}
    generate_all(all_tokens)
    generate_tokens_json(all_tokens)
    generate_template()
    print(f"Generated ports in {OUT}")
    print(f"Generated palette in {PALETTE_OUT}")
    print(f"Generated template in {TEMPLATE_OUT}")


if __name__ == "__main__":
    main()
