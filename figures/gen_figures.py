#!/usr/bin/env python3
"""Validate the deterministic SVG figures and optionally create PNG previews.

The figures intentionally remain at country / macro-region scale.  They contain
no facility coordinates, target lists, or attack-effect estimates.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree


FIGURE_DIR = Path(__file__).resolve().parent
FIGURES = [
    FIGURE_DIR / "fig_1_dependency_flow.svg",
    FIGURE_DIR / "fig_2_time_horizons.svg",
    FIGURE_DIR / "fig_3_ukraine_translation.svg",
    FIGURE_DIR / "fig_4_china_provincial_supply_chain.svg",
    FIGURE_DIR / "fig_5_china_coastal_theater_context.svg",
]

FORBIDDEN_PHRASES = (
    "target coordinates",
    "strike sequence",
    "weapon assignment",
    "設施座標",
    "攻擊排序",
    "武器選擇",
)


def validate() -> None:
    for figure in FIGURES:
        if not figure.exists():
            raise FileNotFoundError(figure)
        ElementTree.parse(figure)
        text = figure.read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase.lower() in text:
                raise ValueError(f"unsafe phrase in {figure.name}: {phrase}")
        if "<title" not in text or "<desc" not in text:
            raise ValueError(f"accessibility metadata missing: {figure.name}")


def render_with_sharp(figure: Path, desired: Path) -> bool:
    """Render with the bundled Node/sharp runtime while preserving aspect ratio."""

    bundled_root = (
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node"
    )
    node = bundled_root / "bin/node"
    node_modules = bundled_root / "node_modules"
    if not node.exists() or not node_modules.exists():
        return False

    javascript = (
        "const sharp=require('sharp');"
        "sharp(process.argv[1],{density:180})"
        ".resize({width:1800,withoutEnlargement:false})"
        ".png().toFile(process.argv[2])"
        ".catch(e=>{console.error(e);process.exit(1)});"
    )
    runtime_env = os.environ.copy()
    runtime_env["NODE_PATH"] = str(node_modules)
    subprocess.run(
        [str(node), "-e", javascript, str(figure), str(desired)],
        check=True,
        env=runtime_env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def render_previews() -> None:
    preview_dir = FIGURE_DIR / "previews"
    preview_dir.mkdir(exist_ok=True)
    for figure in FIGURES:
        desired = preview_dir / f"{figure.stem}.png"
        if render_with_sharp(figure, desired):
            continue

        qlmanage = shutil.which("qlmanage")
        if not qlmanage:
            print(
                "sharp and qlmanage unavailable; "
                f"PNG preview skipped for {figure.name}."
            )
            continue
        subprocess.run(
            [qlmanage, "-t", "-s", "1800", "-o", str(preview_dir), str(figure)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        generated = preview_dir / f"{figure.name}.png"
        if generated.exists() and generated != desired:
            generated.replace(desired)


def main() -> int:
    validate()
    render_previews()
    print(f"Validated {len(FIGURES)} SVG figures.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
