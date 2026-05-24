#!/usr/bin/env python3
"""Generate Sequoia light themes from dark themes (same accent colors, inverted UI)."""

import json
import re
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
THEMES = ROOT / "themes"

# Structural dark → light (longer alpha suffixes first)
HEX_REPLACEMENTS = [
    ("#fdfdfee6", "#43444de6"),
    ("#817c9c80", "#817c9c50"),
    ("#817c9c66", "#817c9c40"),
    ("#817c9c4d", "#817c9c30"),
    ("#817c9c26", "#817c9c24"),
    ("#817c9c14", "#817c9c18"),
    ("#1917244d", "#817c9c28"),
    ("#0f1014", "#fafafc"),
    ("#111216", "#f3f3f6"),
    ("#131317", "#e8e8ed"),
    ("#11121600", "#f3f3f600"),
    ("#fdfdfe90", "#43444d90"),
    ("#fdfdfe80", "#43444d80"),
    ("#fdfdfe", "#43444d"),
    ("#868690", "#43444d"),
    ("#575861", "#626370"),
    ("#43444d", "#787983"),
]

NOTEBOOK_LIGHT = {
    "notebook.editorBackground": "#fafafc",
    "notebook.cellEditorBackground": "#f3f3f6",
    "notebook.cellHoverBackground": "#e8e8ed",
    "notebook.focusedCellBackground": "#f3f3f6",
    "notebook.selectedCellBackground": "#e8e8ed",
    "notebook.symbolHighlightBackground": "#817c9c18",
    "notebook.outputContainerBackgroundColor": "#f3f3f6",
}

# Shared structural bump for light themes (backgrounds, text, selection overlays).
LIGHT_BUMP_BASE = [
    ("#fafafc", "#edeef2"),
    ("#f3f3f6", "#e2e3e8"),
    ("#e8e8ed", "#d4d5dc"),
    ("#43444d", "#282930"),
    ("#626370", "#42434e"),
    ("#787983", "#565760"),
    ("#817c9c18", "#817c9c28"),
    ("#817c9c24", "#817c9c38"),
    ("#817c9c30", "#817c9c45"),
]

MOONLIGHT_ACCENT_BUMP = [
    ("#8eb6f5", "#4a85d4"),
    ("#ffbb88", "#d9884a"),
    ("#c58fff", "#9a5fd9"),
    ("#f58ee0", "#c94da8"),
    ("#9898a6", "#6a6a78"),
]

RETRO_ACCENT_BUMP = [
    ("#648f68", "#4a704e"),
    ("#829fa7", "#5f7982"),
    ("#5c87a4", "#456a82"),
    ("#a27e57", "#8a6539"),
    ("#da674b", "#bf5238"),
    ("#e8b246", "#c99730"),
]

# Invert the monochrome gray ramp for light backgrounds (bright accents → dark).
MONOCHROME_ACCENT_BUMP = [
    ("#e2e4ed", "#25262d"),
    ("#d3d5de", "#50535e"),
    ("#b6bac8", "#454752"),
    ("#999eb2", "#525666"),
    ("#7c829d", "#5f6370"),
    ("#626983", "#2e3038"),
]

BUMP_PROFILES = {
    "moonlight": LIGHT_BUMP_BASE + MOONLIGHT_ACCENT_BUMP,
    "retro": LIGHT_BUMP_BASE + RETRO_ACCENT_BUMP,
    "monochrome": LIGHT_BUMP_BASE + MONOCHROME_ACCENT_BUMP,
}

NOTEBOOK_LIGHT_BUMP = {
    "notebook.editorBackground": "#edeef2",
    "notebook.cellEditorBackground": "#e2e3e8",
    "notebook.cellHoverBackground": "#d4d5dc",
    "notebook.focusedCellBackground": "#e2e3e8",
    "notebook.selectedCellBackground": "#d4d5dc",
    "notebook.symbolHighlightBackground": "#817c9c28",
    "notebook.outputContainerBackgroundColor": "#e2e3e8",
}

VARIANTS = [
    {
        "source": "sequoia-moonlight.json",
        "target": "sequoia-moonlight-light.json",
        "name": "Sequoia Moonlight Light",
        "bump": "moonlight",
    },
    {
        "source": "sequoia-monochrome.json",
        "target": "sequoia-monochrome-light.json",
        "name": "Sequoia Monochrome Light",
        "bump": "monochrome",
    },
    {
        "source": "sequoia-retro.json",
        "target": "sequoia-retro-light.json",
        "name": "Sequoia Retro Light",
        "bump": "retro",
    },
]


def replace_hex(value: str, replacements: list[tuple[str, str]]) -> str:
    if not isinstance(value, str) or not value.startswith("#"):
        return value
    lower = value.lower()
    for old, new in replacements:
        if lower == old:
            return new
        if lower.startswith(old) and len(lower) > len(old):
            return new + lower[len(old) :]
    # Preserve alpha suffixes on unknown bases
    match = re.fullmatch(r"(#[0-9a-f]{6})([0-9a-f]{2})?", lower)
    if not match:
        return value
    base = match.group(1)
    alpha = match.group(2) or ""
    for old, new in replacements:
        if base == old and not alpha:
            return new
    return value


def transform_node(node, replacements: list[tuple[str, str]]):
    if isinstance(node, dict):
        return {k: transform_node(v, replacements) for k, v in node.items()}
    if isinstance(node, list):
        return [transform_node(v, replacements) for v in node]
    if isinstance(node, str):
        return replace_hex(node, replacements)
    return node


def bump_theme(theme: dict, profile: str):
    bumped = transform_node(theme, BUMP_PROFILES[profile])
    bumped["colors"].update(NOTEBOOK_LIGHT_BUMP)
    return bumped


def fix_monochrome_light_comments(theme: dict):
    for rule in theme.get("tokenColors", []):
        scope = rule.get("scope")
        if scope == ["comment"] or scope == "comment":
            rule.setdefault("settings", {})["foreground"] = "#9da2ad"


def fix_light_contrast(theme: dict):
    """Fix tokens that stay white after dark→light inversion."""
    colors = theme["colors"]
    fixes = {
        "tab.activeForeground": "#282930",
        "tab.activeBorderTop": "#282930",
        "list.deemphasizedForeground": "#565760",
    }
    for key, value in fixes.items():
        if colors.get(key) in ("#fff", "#ffffff", "#fafafc", "#fdfdfe"):
            colors[key] = value


def fix_button_contrast(colors: dict):
    """Keep accent button text dark on warm accents."""
    accent_keys = (
        "button.background",
        "activityBarBadge.background",
        "badge.background",
        "progressBar.background",
    )
    for key in accent_keys:
        if key in colors and colors[key].startswith("#"):
            colors["button.foreground"] = "#0f1014"
            colors["activityBarBadge.foreground"] = "#0f1014"
            colors["badge.foreground"] = "#0f1014"
            colors["extensionButton.prominentForeground"] = "#0f1014"
            break


def generate(source: Path, target: Path, name: str, bump=None):
    theme = json.loads(source.read_text(encoding="utf-8"))
    theme = transform_node(theme, HEX_REPLACEMENTS)
    theme["name"] = name
    theme["type"] = "light"
    theme["colors"].update(NOTEBOOK_LIGHT)
    fix_button_contrast(theme["colors"])
    fix_light_contrast(theme)
    if bump:
        theme = bump_theme(theme, bump)
        fix_button_contrast(theme["colors"])
        fix_light_contrast(theme)
        if bump == "monochrome":
            fix_monochrome_light_comments(theme)
    target.write_text(json.dumps(theme, indent=2) + "\n", encoding="utf-8")
    label = f"{target.name} (bumped {bump})" if bump else target.name
    print(f"Wrote {label}")


def main():
    for variant in VARIANTS:
        generate(
            THEMES / variant["source"],
            THEMES / variant["target"],
            variant["name"],
            bump=variant.get("bump"),
        )


if __name__ == "__main__":
    main()
