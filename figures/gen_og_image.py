#!/usr/bin/env python3
"""Render the 1200x630 Open Graph share card into assets/og-image.png.

The card reuses the site palette from assets/styles.css. It carries no data,
so it needs no source review; it only has to survive social-preview cropping.

Font selection is checked, not assumed. Several macOS CJK collections expose a
face that silently drops Traditional Chinese glyphs, which renders as missing
characters instead of an error. pick_font compares each glyph against the
font's own .notdef and rejects a face that cannot draw the required text.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "og-image.png"

WIDTH, HEIGHT = 1200, 630
INK = (23, 38, 64)
STRIP = (16, 26, 44)
GRID = (30, 47, 76)
PAPER = (243, 239, 229)
RED = (219, 58, 52)
CYAN = (120, 195, 200)
MUTED = (150, 163, 186)

BOUNDARY = "公開資料 · 非作戰化研究 · 不含設施座標、部隊部署或目標資訊"
SUBTITLE = "省級經濟功能 · 供應鏈關聯 · 臺海韌性脈絡"
META = "31 個省級行政區 · 公開資料互動圖鑑"

# (path, face index). Latin display faces for the SEE THROUGH CHINA wordmark.
SERIF_CANDIDATES = [
    ("/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf", 0),
    ("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 0),
    ("/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf", 0),
    ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 0),
]
# CJK faces verified to cover Traditional Chinese, closest first to the
# Noto Sans TC used on the site.
SANS_CANDIDATES = [
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),        # Heiti TC Medium
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 2),      # Hiragino Sans GB W6
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 2),   # Songti TC Bold
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansTC-Medium.otf", 0),
]


def glyph_pixels(font: ImageFont.FreeTypeFont, char: str) -> bytes:
    box = int(font.size * 2)
    tile = Image.new("L", (box, box), 0)
    ImageDraw.Draw(tile).text((box // 4, box // 4), char, font=font, fill=255)
    return tile.tobytes()


def renders_all(font: ImageFont.FreeTypeFont, text: str) -> bool:
    """True when every non-space character draws something other than .notdef."""
    # U+FFF0 is permanently unassigned, so it always resolves to .notdef.
    notdef = glyph_pixels(font, "￰")
    blank = Image.new("L", (int(font.size * 2), int(font.size * 2)), 0).tobytes()
    for char in text:
        if char.isspace():
            continue
        try:
            drawn = glyph_pixels(font, char)
        except OSError:
            return False
        if drawn == blank or drawn == notdef:
            return False
    return True


def pick_font(candidates: list[tuple[str, int]], size: int, text: str) -> ImageFont.FreeTypeFont:
    tried = []
    for path, index in candidates:
        if not Path(path).exists():
            continue
        try:
            font = ImageFont.truetype(path, size, index=index)
        except OSError:
            continue
        if renders_all(font, text):
            return font
        tried.append(f"{path}#{index}")
    raise SystemExit(
        "No font covers the required glyphs.\n"
        f"  text: {text}\n"
        f"  rejected: {tried or 'none found on this system'}\n"
        "  Add a font path to SERIF_CANDIDATES or SANS_CANDIDATES."
    )


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
    left, _, right, _ = draw.textbbox((0, 0), text, font=font)
    return right - left


def main() -> int:
    image = Image.new("RGB", (WIDTH, HEIGHT), INK)
    draw = ImageDraw.Draw(image)

    # Faint grid, echoing .hero-grid on the site.
    for x in range(0, WIDTH, 60):
        draw.line([(x, 0), (x, HEIGHT)], fill=GRID, width=1)
    for y in range(0, HEIGHT, 60):
        draw.line([(0, y), (WIDTH, y)], fill=GRID, width=1)

    # Boundary strip along the top, same wording as the site banner.
    draw.rectangle([(0, 0), (WIDTH, 56)], fill=STRIP)
    draw.text((64, 28), BOUNDARY, font=pick_font(SANS_CANDIDATES, 18, BOUNDARY),
              fill=MUTED, anchor="lm")

    display = pick_font(SERIF_CANDIDATES, 126, "SEETHROUGHCINA")
    draw.text((64, 158), "SEE", font=display, fill=PAPER, anchor="lt")
    draw.text((64, 276), "THROUGH", font=display, fill=PAPER, anchor="lt")
    draw.text((160, 394), "CHINA", font=display, fill=RED, anchor="lt")

    # Accent rule sized to the widest display line.
    draw.rectangle([(64, 136), (64 + text_width(draw, "THROUGH", display), 142)], fill=RED)

    draw.text((64, 552), SUBTITLE, font=pick_font(SANS_CANDIDATES, 25, SUBTITLE),
              fill=CYAN, anchor="lt")
    draw.text((WIDTH - 64, 555), META, font=pick_font(SANS_CANDIDATES, 19, META),
              fill=MUTED, anchor="rt")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, "PNG", optimize=True)
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({WIDTH}x{HEIGHT}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
