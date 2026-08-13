#!/usr/bin/env python3
"""Build Figure 1 from the OpenStreetMap standard world-map tiles.

Only the low-zoom tiles required for the displayed world viewport are fetched.
They are cached for at least seven days and requested with an identifying
User-Agent, following the OSMF Tile Usage Policy.  The overlay remains at
country / macro-region scale and contains no facility locations.
"""

from __future__ import annotations

import base64
import json
import math
import time
import urllib.error
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image


FIGURE_DIR = Path(__file__).resolve().parent
CACHE_DIR = FIGURE_DIR / "osm_tile_cache"
BASE_MAP = FIGURE_DIR / "osm_world_base.png"
OUTPUT_SVG = FIGURE_DIR / "fig_1_dependency_flow.svg"

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = (
    "TaiwanStrategicDependencyResearchMap/1.0 "
    "(+https://www.openstreetmap.org/copyright)"
)
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60
ZOOM = 2
TILE_SIZE = 256

CANVAS_W, CANVAS_H = 1600, 1080
MAP_X, MAP_Y, MAP_W = 50, 120, 1500
NORTH, SOUTH = 80.0, -60.0


def tile_paths(x: int, y: int) -> tuple[Path, Path]:
    folder = CACHE_DIR / str(ZOOM) / str(x)
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{y}.png", folder / f"{y}.json"


def load_tile(x: int, y: int) -> Image.Image:
    tile_path, metadata_path = tile_paths(x, y)
    now = time.time()
    if tile_path.exists() and now - tile_path.stat().st_mtime < CACHE_TTL_SECONDS:
        return Image.open(tile_path).convert("RGB")

    metadata: dict[str, str] = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    headers = {"User-Agent": USER_AGENT}
    if metadata.get("etag"):
        headers["If-None-Match"] = metadata["etag"]
    if metadata.get("last_modified"):
        headers["If-Modified-Since"] = metadata["last_modified"]

    request = urllib.request.Request(
        TILE_URL.format(z=ZOOM, x=x, y=y), headers=headers
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            tile_path.write_bytes(payload)
            metadata_path.write_text(
                json.dumps(
                    {
                        "etag": response.headers.get("ETag", ""),
                        "last_modified": response.headers.get("Last-Modified", ""),
                        "source": TILE_URL,
                        "fetched_unix": str(int(now)),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
    except urllib.error.HTTPError as error:
        if error.code == 304 and tile_path.exists():
            tile_path.touch()
        else:
            raise

    time.sleep(0.12)
    return Image.open(tile_path).convert("RGB")


def mercator_pixel_y(latitude: float, world_size: int) -> float:
    latitude = max(-85.05112878, min(85.05112878, latitude))
    radians = math.radians(latitude)
    return (1.0 - math.asinh(math.tan(radians)) / math.pi) * world_size / 2.0


def build_base_map() -> tuple[Image.Image, float]:
    side = TILE_SIZE * (2**ZOOM)
    mosaic = Image.new("RGB", (side, side), "white")
    for x in range(2**ZOOM):
        for y in range(2**ZOOM):
            mosaic.paste(load_tile(x, y), (x * TILE_SIZE, y * TILE_SIZE))

    crop_top = round(mercator_pixel_y(NORTH, side))
    crop_bottom = round(mercator_pixel_y(SOUTH, side))
    cropped = mosaic.crop((0, crop_top, side, crop_bottom))
    map_height = MAP_W * cropped.height / cropped.width
    cropped.save(BASE_MAP, optimize=True)
    return cropped, map_height


def map_point(lon: float, lat: float, map_height: float) -> tuple[float, float]:
    side = TILE_SIZE * (2**ZOOM)
    top = mercator_pixel_y(NORTH, side)
    bottom = mercator_pixel_y(SOUTH, side)
    x = MAP_X + (lon + 180.0) / 360.0 * MAP_W
    normalized_y = (mercator_pixel_y(lat, side) - top) / (bottom - top)
    y = MAP_Y + normalized_y * map_height
    return x, y


def f(value: float) -> str:
    return f"{value:.1f}"


def build_svg(base_map: Image.Image, map_height: float) -> str:
    encoded = base64.b64encode(BASE_MAP.read_bytes()).decode("ascii")
    americas = map_point(-97, 38, map_height)
    partners = map_point(8, 46, map_height)
    west_asia = map_point(48, 25, map_height)
    russia = map_point(75, 56, map_height)
    china = map_point(105, 35, map_height)
    taiwan = map_point(121, 23.7, map_height)

    def curve(
        start: tuple[float, float],
        control: tuple[float, float],
        end: tuple[float, float],
        color: str,
        marker: str,
        width: float,
        dash: str = "",
        opacity: float = 0.88,
    ) -> str:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        return (
            f'<path d="M {f(start[0])} {f(start[1])} Q {f(control[0])} '
            f'{f(control[1])} {f(end[0])} {f(end[1])}" fill="none" '
            f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'opacity="{opacity}" marker-end="url(#{marker})"{dash_attr}/>'
        )

    map_bottom = MAP_Y + map_height
    paths = [
        curve(americas, map_point(-5, 72, map_height), china, "#009E73", "green", 7),
        curve(americas, map_point(-25, 8, map_height), taiwan, "#009E73", "green", 4, opacity=0.75),
        curve(west_asia, map_point(76, 18, map_height), china, "#E69F00", "orange", 7),
        curve(west_asia, map_point(88, 2, map_height), taiwan, "#E69F00", "orange", 5, opacity=0.78),
        curve(russia, map_point(92, 51, map_height), china, "#009E73", "green", 5),
        curve(partners, map_point(58, 66, map_height), china, "#0072B2", "blue", 5),
        curve(partners, map_point(72, -5, map_height), taiwan, "#0072B2", "blue", 5),
        curve(china, map_point(62, 28, map_height), partners, "#CC79A7", "purple", 4, "11 8", 0.85),
        curve(taiwan, map_point(65, -28, map_height), partners, "#CC79A7", "purple", 4, "11 8", 0.85),
    ]

    def region_label(
        point: tuple[float, float],
        title: str,
        detail: str,
        dx: float,
        dy: float,
        width: int,
    ) -> str:
        x, y = point[0] + dx, point[1] + dy
        return f"""
        <g transform="translate({f(x)} {f(y)})" filter="url(#shadow)">
          <rect x="0" y="0" width="{width}" height="62" rx="10" fill="#FFFFFF" fill-opacity="0.91" stroke="#CBD5E1"/>
          <text x="14" y="25" class="region-title">{title}</text>
          <text x="14" y="48" class="region-text">{detail}</text>
        </g>"""

    labels = [
        region_label(americas, "美洲農產區", "糧食、油籽、飼料", -105, 28, 205),
        region_label(partners, "全球市場／伙伴", "外需、金融、設備與材料", -120, 35, 245),
        region_label(west_asia, "西亞能源市場", "原油、LNG 與石化投入", -118, 38, 230),
        region_label(russia, "俄羅斯／中亞", "陸路能源與大宗商品", -95, -78, 225),
        region_label(china, "中國", "國內緩衝＋跨境投入", -58, 30, 200),
        region_label(taiwan, "臺灣", "島嶼型高外部連結", 22, -22, 195),
    ]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img" aria-labelledby="title desc">
  <title id="title">以 OpenStreetMap 為底圖的中臺宏觀跨境依賴流向圖</title>
  <desc id="desc">OpenStreetMap 世界底圖上的國家與大區域能源、糧食、科技、製造及金融依賴示意，不含設施位置，箭頭不表示精確航路。</desc>
  <defs>
    <marker id="orange" markerWidth="11" markerHeight="11" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#E69F00"/></marker>
    <marker id="green" markerWidth="11" markerHeight="11" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#009E73"/></marker>
    <marker id="blue" markerWidth="11" markerHeight="11" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#0072B2"/></marker>
    <marker id="purple" markerWidth="11" markerHeight="11" refX="9" refY="5" orient="auto"><path d="M0,0 L10,5 L0,10 Z" fill="#CC79A7"/></marker>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#1F2937" flood-opacity="0.18"/></filter>
    <clipPath id="map-clip"><rect x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{f(map_height)}" rx="16"/></clipPath>
    <style>
      .title{{font:700 34px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#1F2937}}
      .subtitle{{font:400 18px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#5B6472}}
      .region-title{{font:700 17px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#23313F}}
      .region-text{{font:400 13px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#425466}}
      .legend{{font:600 14px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#303846}}
      .note{{font:400 13px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#4B5563}}
    </style>
  </defs>
  <rect width="{CANVAS_W}" height="{CANVAS_H}" fill="#FAFAF7"/>
  <text x="50" y="50" class="title">中臺宏觀跨境依賴流向圖</text>
  <text x="50" y="84" class="subtitle">OpenStreetMap 世界底圖；箭頭為國家／大區域層級的依賴方向，不表示精確航路。</text>
  <g clip-path="url(#map-clip)">
    <image x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{f(map_height)}" href="data:image/png;base64,{encoded}" preserveAspectRatio="none"/>
    <rect x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{f(map_height)}" fill="#FFFFFF" opacity="0.20"/>
    {''.join(paths)}
    <circle cx="{f(china[0])}" cy="{f(china[1])}" r="15" fill="#D55E00" fill-opacity="0.82" stroke="#FFFFFF" stroke-width="4"/>
    <circle cx="{f(taiwan[0])}" cy="{f(taiwan[1])}" r="10" fill="#2A9D8F" stroke="#FFFFFF" stroke-width="4"/>
    {''.join(labels)}
    <g transform="translate(74 {f(map_bottom - 105)})" filter="url(#shadow)">
      <rect width="620" height="70" rx="10" fill="#FFFFFF" fill-opacity="0.92" stroke="#CBD5E1"/>
      <line x1="18" y1="22" x2="58" y2="22" stroke="#E69F00" stroke-width="6"/><text x="68" y="27" class="legend">海運能源</text>
      <line x1="182" y1="22" x2="222" y2="22" stroke="#009E73" stroke-width="6"/><text x="232" y="27" class="legend">糧食／陸路供應</text>
      <line x1="395" y1="22" x2="435" y2="22" stroke="#0072B2" stroke-width="6"/><text x="445" y="27" class="legend">設備／金融</text>
      <line x1="18" y1="50" x2="58" y2="50" stroke="#CC79A7" stroke-width="5" stroke-dasharray="9 6"/><text x="68" y="55" class="legend">製造出口與跨境服務</text>
    </g>
    <a href="https://www.openstreetmap.org/copyright" target="_blank">
      <rect x="{MAP_X + MAP_W - 470}" y="{f(map_bottom - 34)}" width="460" height="25" rx="7" fill="#FFFFFF" fill-opacity="0.88"/>
      <text x="{MAP_X + MAP_W - 460}" y="{f(map_bottom - 17)}" class="note">© OpenStreetMap contributors · ODbL · openstreetmap.org/copyright</text>
    </a>
  </g>
  <rect x="{MAP_X}" y="{MAP_Y}" width="{MAP_W}" height="{f(map_height)}" rx="16" fill="none" stroke="#CBD5E1" stroke-width="2"/>
  <text x="50" y="1054" class="note">閱讀方式：依賴須與產能、替代來源、庫存、修復與治理能力共同判讀；本圖不呈現設施或節點。</text>
</svg>
"""


def main() -> int:
    base_map, map_height = build_base_map()
    OUTPUT_SVG.write_text(build_svg(base_map, map_height), encoding="utf-8")
    print(f"Wrote {OUTPUT_SVG.name} using OpenStreetMap world tiles at zoom {ZOOM}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
