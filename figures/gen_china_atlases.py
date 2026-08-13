#!/usr/bin/env python3
"""Generate safe province-level economic and theater-level context maps.

The province map labels only administrative-area economic functions.  The
separate theater map shows broad coastal responsibility directions and public
activity patterns; it never contains unit identifiers, bases, coordinates,
force counts, equipment, readiness, ranges, or movements.
"""

from __future__ import annotations

import csv
import html
import json
import math
import time
import urllib.request
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "figures"
DATA = ROOT / "data"
BASE_MAP = FIGURES / "osm_china_base.png"
CACHE_DIR = FIGURES / "osm_tile_cache"
PROVINCE_CSV = DATA / "china_provincial_supply_chain_atlas.csv"
THEATER_CSV = DATA / "china_coastal_theater_context.csv"
PROVINCE_SVG = FIGURES / "fig_4_china_provincial_supply_chain.svg"
THEATER_SVG = FIGURES / "fig_5_china_coastal_theater_context.svg"
INTERACTIVE_HTML = FIGURES / "china_provincial_supply_chain_atlas.html"

CHINA_BOUNDS = (72.0, 16.0, 136.0, 54.0)
ZOOM = 4
TILE_SIZE = 256
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = (
    "TaiwanStrategicDependencyResearchAtlas/1.0 "
    "(+https://www.openstreetmap.org/copyright)"
)
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60

PROVINCES = {
    "北京市": (116.4, 39.9), "天津市": (117.2, 39.1), "河北省": (114.7, 38.3),
    "山西省": (112.3, 37.5), "內蒙古自治區": (111.7, 43.8), "遼寧省": (123.4, 41.4),
    "吉林省": (125.3, 43.7), "黑龍江省": (127.5, 47.0), "上海市": (121.5, 31.2),
    "江蘇省": (119.0, 32.9), "浙江省": (120.2, 29.2), "安徽省": (117.3, 31.8),
    "福建省": (118.0, 26.1), "江西省": (115.9, 27.6), "山東省": (118.0, 36.4),
    "河南省": (113.6, 34.0), "湖北省": (112.3, 30.9), "湖南省": (112.9, 27.7),
    "廣東省": (113.3, 23.4), "廣西壯族自治區": (108.3, 23.8), "海南省": (109.7, 19.2),
    "重慶市": (106.6, 29.6), "四川省": (103.8, 30.6), "貴州省": (106.7, 26.8),
    "雲南省": (101.5, 24.7), "西藏自治區": (88.5, 31.7), "陝西省": (108.9, 35.2),
    "甘肅省": (103.8, 36.1), "青海省": (96.0, 35.5), "寧夏回族自治區": (106.2, 37.3),
    "新疆維吾爾自治區": (85.6, 41.5),
}

SHORT = {
    "內蒙古自治區": "內蒙古", "廣西壯族自治區": "廣西", "西藏自治區": "西藏",
    "寧夏回族自治區": "寧夏", "新疆維吾爾自治區": "新疆",
}

GROUP_COLORS = {
    "服務創新": "#6C5CE7", "服務貿易": "#8E6BBE", "沿海製造": "#0072B2",
    "內陸製造": "#56B4E9", "農業物流": "#009E73", "農業製造": "#43AA8B",
    "農業資源": "#73A942", "能源數位": "#E69F00", "能源材料": "#D55E00",
    "能源物流": "#F4A261", "能源製造": "#E76F51", "能源邊貿": "#B5651D",
    "邊境物流": "#CC79A7", "邊境服務": "#A06CD5",
}


def mercator_y(lat: float) -> float:
    lat = max(-85.05112878, min(85.05112878, lat))
    r = math.radians(lat)
    return (1 - math.asinh(math.tan(r)) / math.pi) / 2


def world_px(lon: float, lat: float) -> tuple[float, float]:
    world_size = TILE_SIZE * (2**ZOOM)
    return (lon + 180) / 360 * world_size, mercator_y(lat) * world_size


def crop_box() -> tuple[float, float, float, float]:
    west, south, east, north = CHINA_BOUNDS
    x0, y0 = world_px(west, north)
    x1, y1 = world_px(east, south)
    return x0, y0, x1, y1


def map_point(lon: float, lat: float, x: float, y: float, w: float, h: float) -> tuple[float, float]:
    x0, y0, x1, y1 = crop_box()
    px, py = world_px(lon, lat)
    return x + (px - x0) / (x1 - x0) * w, y + (py - y0) / (y1 - y0) * h


def load_tile(tile_x: int, tile_y: int) -> Image.Image:
    path = CACHE_DIR / str(ZOOM) / str(tile_x) / f"{tile_y}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and time.time() - path.stat().st_mtime < CACHE_TTL_SECONDS:
        return Image.open(path).convert("RGB")
    request = urllib.request.Request(
        TILE_URL.format(z=ZOOM, x=tile_x, y=tile_y),
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        path.write_bytes(response.read())
    time.sleep(0.12)
    return Image.open(path).convert("RGB")


def build_china_base() -> None:
    x0, y0, x1, y1 = crop_box()
    first_x, last_x = math.floor(x0 / TILE_SIZE), math.floor((x1 - 1) / TILE_SIZE)
    first_y, last_y = math.floor(y0 / TILE_SIZE), math.floor((y1 - 1) / TILE_SIZE)
    mosaic = Image.new(
        "RGB",
        ((last_x - first_x + 1) * TILE_SIZE, (last_y - first_y + 1) * TILE_SIZE),
        "white",
    )
    for tile_x in range(first_x, last_x + 1):
        for tile_y in range(first_y, last_y + 1):
            mosaic.paste(
                load_tile(tile_x, tile_y),
                ((tile_x - first_x) * TILE_SIZE, (tile_y - first_y) * TILE_SIZE),
            )
    left = round(x0 - first_x * TILE_SIZE)
    top = round(y0 - first_y * TILE_SIZE)
    right = round(x1 - first_x * TILE_SIZE)
    bottom = round(y1 - first_y * TILE_SIZE)
    mosaic.crop((left, top, right, bottom)).save(BASE_MAP, optimize=True)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def label_offset(name: str) -> tuple[int, int]:
    return {
        "北京市": (-12, -13), "天津市": (21, 12), "河北省": (-17, 20),
        "上海市": (25, 8), "江蘇省": (-18, -18), "浙江省": (22, 18),
        "安徽省": (-18, 13), "福建省": (21, 10), "河南省": (-12, -14),
        "湖北省": (15, 16), "重慶市": (18, 10), "廣東省": (12, 18),
        "海南省": (12, 14), "寧夏回族自治區": (18, -10),
    }.get(name, (10, -10))


def svg_base(title: str, subtitle: str, desc: str, body: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1080" viewBox="0 0 1600 1080" role="img" aria-labelledby="title desc">
  <title id="title">{html.escape(title)}</title><desc id="desc">{html.escape(desc)}</desc>
  <defs><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#1F2937" flood-opacity="0.17"/></filter>
  <style>.title{{font:700 34px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#1F2937}}.sub{{font:400 17px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#5B6472}}.label{{font:600 12px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#23313F}}.body{{font:400 15px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#374151}}.head{{font:700 21px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#23313F}}.note{{font:400 13px 'PingFang TC','Noto Sans CJK TC',sans-serif;fill:#4B5563}}</style></defs>
  <rect width="1600" height="1080" fill="#FAFAF7"/><text x="55" y="52" class="title">{html.escape(title)}</text><text x="55" y="84" class="sub">{html.escape(subtitle)}</text>{body}</svg>"""


def make_province_svg(rows: list[dict[str, str]]) -> None:
    x, y, w, h = 55, 120, 1050, 820
    parts = [
        f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="osm_china_base.png" preserveAspectRatio="none"/><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" opacity="0.20"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#CBD5E1" stroke-width="2"/>',
    ]
    for row in rows:
        name = row["province"]
        lon, lat = PROVINCES[name]
        px, py = map_point(lon, lat, x, y, w, h)
        dx, dy = label_offset(name)
        color = GROUP_COLORS[row["role_group"]]
        label = SHORT.get(name, name.removesuffix("省").removesuffix("市"))
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="{color}" stroke="#FFFFFF" stroke-width="2"><title>{html.escape(name)}｜{html.escape(row["public_function"])}</title></circle>')
        parts.append(f'<text x="{px+dx:.1f}" y="{py+dy:.1f}" class="label" paint-order="stroke" stroke="#FFFFFF" stroke-width="3">{html.escape(label)}</text>')

    panel_x = 1140
    parts.extend([
        f'<g transform="translate({panel_x} 120)" filter="url(#shadow)"><rect width="405" height="820" rx="16" fill="#FFFFFF" fill-opacity="0.95" stroke="#D7DEE5"/><text x="25" y="42" class="head">31 省級經濟功能</text><text x="25" y="72" class="body">點位代表省級行政區，不是設施。</text>',
    ])
    legend_groups = [
        ("沿海製造", "港航／出口／先進製造"), ("內陸製造", "公鐵／長江／承接製造"),
        ("能源材料", "煤油氣／電力／礦產材料"), ("農業物流", "糧食／食品／冷鏈分撥"),
        ("邊境物流", "陸路口岸／跨境商貿"), ("服務創新", "治理／金融／研發／數位"),
    ]
    for idx, (group, desc) in enumerate(legend_groups):
        yy = 120 + idx * 74
        parts.append(f'<circle cx="35" cy="{yy}" r="9" fill="{GROUP_COLORS[group]}"/><text x="58" y="{yy-2}" class="label">{group}</text><text x="58" y="{yy+22}" class="body">{desc}</text>')
    parts.append('<line x1="25" y1="575" x2="380" y2="575" stroke="#D7DEE5"/><text x="25" y="610" class="head">欄位</text><text x="25" y="643" class="body">基礎設施類型（非設施清單）</text><text x="25" y="674" class="body">公共與經濟功能</text><text x="25" y="705" class="body">代表性產品／產業群</text><text x="25" y="736" class="body">主要上游投入與下游連結</text><text x="25" y="790" class="note">完整內容請開啟互動圖或 CSV。</text></g>')
    parts.append(f'<a href="https://www.openstreetmap.org/copyright"><rect x="680" y="{y+h-34}" width="410" height="25" rx="7" fill="#FFFFFF" fill-opacity="0.9"/><text x="690" y="{y+h-17}" class="note">© OpenStreetMap contributors · ODbL · openstreetmap.org/copyright</text></a>')
    parts.append('<text x="55" y="995" class="note">用途：產業政策、供應鏈研究與韌性規劃。排除設施名稱、座標、容量、瓶頸與軍事部署。</text>')
    PROVINCE_SVG.write_text(svg_base("中國大陸省級經濟與供應鏈圖譜", "31 個省、自治區與直轄市；標註省級功能與代表產業，不呈現設施位置。", "以 OpenStreetMap 為底圖的中國大陸省級經濟與供應鏈標註圖。", "".join(parts)), encoding="utf-8")


def make_theater_svg() -> None:
    x, y, w, h = 55, 120, 1050, 820
    parts = [f'<image x="{x}" y="{y}" width="{w}" height="{h}" href="osm_china_base.png" preserveAspectRatio="none"/><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#FFFFFF" opacity="0.25"/>', f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="none" stroke="#CBD5E1" stroke-width="2"/>']
    zones = [
        ("北部戰區層級", 124.0, 40.8, 132.5, 43.5, "#5B8FF9", "黃海／東北方向"),
        ("東部戰區層級", 122.0, 29.0, 135.0, 27.5, "#E76F51", "東海／臺灣方向"),
        ("南部戰區層級", 112.0, 22.0, 121.0, 16.5, "#2A9D8F", "南海方向／可跨區支援"),
    ]
    for name, lon1, lat1, lon2, lat2, color, label in zones:
        sx, sy = map_point(lon1, lat1, x, y, w, h)
        ex, ey = map_point(lon2, lat2, x, y, w, h)
        parts.append(f'<path d="M {sx:.1f} {sy:.1f} Q {(sx+ex)/2+50:.1f} {(sy+ey)/2-45:.1f} {ex:.1f} {ey:.1f}" fill="none" stroke="{color}" stroke-width="18" stroke-linecap="round" opacity="0.55"/>')
        parts.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="13" fill="{color}" stroke="#FFFFFF" stroke-width="4"/><text x="{sx-70:.1f}" y="{sy-25:.1f}" class="head" paint-order="stroke" stroke="#FFFFFF" stroke-width="5">{name}</text><text x="{sx-55:.1f}" y="{sy+35:.1f}" class="body" paint-order="stroke" stroke="#FFFFFF" stroke-width="4">{label}</text>')
    parts.append('<g transform="translate(1140 120)" filter="url(#shadow)"><rect width="405" height="820" rx="16" fill="#FFFFFF" fill-opacity="0.96" stroke="#D7DEE5"/><text x="25" y="42" class="head">讀圖邊界</text><text x="25" y="82" class="body">• 僅為戰區層級責任方向</text><text x="25" y="117" class="body">• 不代表實際部署位置</text><text x="25" y="152" class="body">• 不與基礎設施共圖</text><line x1="25" y1="185" x2="380" y2="185" stroke="#D7DEE5"/><text x="25" y="225" class="head">公開活動類型</text><text x="25" y="265" class="body">聯合指揮與戰備警巡</text><text x="25" y="302" class="body">海空聯合演訓</text><text x="25" y="339" class="body">封鎖相關演訓（東部方向）</text><text x="25" y="376" class="body">灰色地帶與海警協同</text><text x="25" y="413" class="body">跨戰區支援</text><line x1="25" y1="450" x2="380" y2="450" stroke="#D7DEE5"/><text x="25" y="490" class="head">明確排除</text><text x="25" y="530" class="body">部隊番號／基地／座標</text><text x="25" y="567" class="body">兵力／裝備／戰備狀態</text><text x="25" y="604" class="body">射程／行動半徑／調動時間</text><text x="25" y="641" class="body">即時或可預測的部署資訊</text><text x="25" y="730" class="note">來源：臺灣國防部 2025 國防報告；</text><text x="25" y="755" class="note">美國國防部 2025 中國軍力報告。</text></g>')
    parts.append(f'<a href="https://www.openstreetmap.org/copyright"><rect x="680" y="{y+h-34}" width="410" height="25" rx="7" fill="#FFFFFF" fill-opacity="0.9"/><text x="690" y="{y+h-17}" class="note">© OpenStreetMap contributors · ODbL · openstreetmap.org/copyright</text></a>')
    parts.append('<text x="55" y="995" class="note">本圖描述宏觀責任方向與公開活動類型，不是部隊部署圖、目標圖或即時態勢圖。</text>')
    THEATER_SVG.write_text(svg_base("中國沿海戰區級態勢概覽（非部署圖）", "戰區責任方向與公開活動型態；不標示部隊、基地、兵力、裝備或即時位置。", "北部、東部與南部戰區層級的沿海責任方向概覽。", "".join(parts)), encoding="utf-8")


def make_interactive(rows: list[dict[str, str]]) -> None:
    points = []
    for row in rows:
        copy = dict(row)
        copy["lon"], copy["lat"] = PROVINCES[row["province"]]
        copy["color"] = GROUP_COLORS[row["role_group"]]
        points.append(copy)
    payload = json.dumps(points, ensure_ascii=False).replace("</", "<\\/")
    INTERACTIVE_HTML.write_text(f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>中國大陸省級經濟與供應鏈圖譜</title><link rel="stylesheet" href="../assets/vendor/leaflet/leaflet.css"><style>html,body,#map{{height:100%;margin:0}}body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang TC",sans-serif}}.notice{{position:absolute;z-index:1000;top:12px;left:50px;right:50px;max-width:720px;background:#fffffff0;padding:12px 16px;border-radius:10px;box-shadow:0 2px 12px #0002}}.popup b{{font-size:17px}}.popup dt{{font-weight:700;margin-top:8px}}.popup dd{{margin:2px 0 0}}</style></head><body><div class="notice"><b>中國大陸 31 省級經濟與供應鏈圖譜</b><br>點選省級標記查看公共功能、產業、上游投入與下游連結。標記是行政區代表點，不是設施位置。</div><div id="map"></div><script src="../assets/vendor/leaflet/leaflet.js"></script><script>const data={payload};const map=L.map('map',{{zoomControl:true,minZoom:3,maxZoom:7}}).setView([35,104],4);L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a> · ODbL'}}).addTo(map);const esc=s=>String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));for(const p of data){{const m=L.circleMarker([p.lat,p.lon],{{radius:8,color:'#fff',weight:2,fillColor:p.color,fillOpacity:.9}}).addTo(map);m.bindTooltip(esc(p.province)+'｜'+esc(p.role_group));m.bindPopup(`<div class="popup"><b>${{esc(p.province)}}</b>　${{esc(p.role_group)}}<dl><dt>基礎設施類型</dt><dd>${{esc(p.infrastructure_types)}}</dd><dt>公共與經濟功能</dt><dd>${{esc(p.public_function)}}</dd><dt>代表產品／產業群</dt><dd>${{esc(p.representative_products_and_clusters)}}</dd><dt>主要上游投入</dt><dd>${{esc(p.major_upstream_inputs)}}</dd><dt>主要下游連結</dt><dd>${{esc(p.main_downstream_links)}}</dd><dt>信心</dt><dd>${{esc(p.confidence)}}</dd></dl><small>不含設施名稱、座標、容量、瓶頸或軍事部署。</small></div>`,{{maxWidth:440}});}}</script></body></html>""", encoding="utf-8")


def main() -> int:
    build_china_base()
    rows = read_rows(PROVINCE_CSV)
    if len(rows) != 31 or set(PROVINCES) != {r["province"] for r in rows}:
        raise ValueError("province data must contain exactly the configured 31 units")
    make_province_svg(rows)
    make_theater_svg()
    make_interactive(rows)
    print("Generated province atlas, interactive map, and theater-level context map.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
