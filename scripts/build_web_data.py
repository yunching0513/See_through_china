#!/usr/bin/env python3
"""Build the website's static data bundle from reviewed CSV files."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

PROVINCE_COORDINATES = {
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

ROLE_COLORS = {
    "服務創新": "#6c5ce7", "服務貿易": "#8e6bbe", "沿海製造": "#255f85",
    "內陸製造": "#4f9bb7", "農業物流": "#16866c", "農業製造": "#43aa8b",
    "農業資源": "#73a942", "能源數位": "#d98b00", "能源材料": "#cf5233",
    "能源物流": "#e38b4d", "能源製造": "#d85a49", "能源邊貿": "#a96231",
    "邊境物流": "#b94d88", "邊境服務": "#8a62b2",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / "data" / name).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    provinces = read_csv("china_provincial_supply_chain_atlas.csv")
    if len(provinces) != 31:
        raise ValueError("Expected exactly 31 province-level records")
    for province in provinces:
        lon, lat = PROVINCE_COORDINATES[province["province"]]
        province.update(lon=lon, lat=lat, color=ROLE_COLORS[province["role_group"]])

    payload = {
        "updated": "2026-08-13",
        "provinces": provinces,
        "dependencies": read_csv("dependency_assessment.csv"),
        "theaters": read_csv("china_coastal_theater_context.csv"),
        "roleColors": ROLE_COLORS,
    }
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    (ROOT / "assets" / "data.js").write_text(
        f"window.ATLAS_DATA={encoded};\n",
        encoding="utf-8",
    )
    print(f"Built assets/data.js with {len(provinces)} province-level records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
