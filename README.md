# 臺海衝突下的戰略依賴與國家韌性研究（非作戰化版本）

本工作區收錄一份以公開資料為基礎的初版政策研究。經濟資料可細分至省級行政區，但不細分至設施；軍事資訊僅到戰區級責任方向且與基礎設施分圖呈現。不包含設施座標、部隊部署、武力打擊點、攻擊排序、癱瘓方法或損害最佳化。

## 主要成果

- `report/台海衝突_戰略依賴與國家韌性_研究底稿_v1.md`：完整研究底稿。
- `research_notes/phase1_scoping.md`：研究問題、範圍與方法。
- `research_notes/search_and_review_log.md`：檢索策略、來源偏差與審查紀錄。
- `data/evidence_matrix.csv`：來源—主張—品質矩陣。
- `data/dependency_assessment.csv`：國家層級的系統依賴比較資料。
- `data/china_provincial_supply_chain_atlas.csv`：中國大陸 31 個省級行政區的經濟功能、代表產品與供應鏈關聯。
- `data/china_coastal_theater_context.csv`：北部、東部、南部戰區層級的沿海責任方向與公開活動型態；不是部署資料。
- `figures/fig_1_dependency_flow.svg`：以 OpenStreetMap 世界底圖呈現的宏觀依賴流向圖。
- `figures/fig_2_time_horizons.svg`：短、中、長期壓力機制圖。
- `figures/fig_3_ukraine_translation.svg`：烏克蘭經驗轉譯至臺灣的韌性架構。
- `figures/fig_4_china_provincial_supply_chain.svg`：OSM 省級經濟與供應鏈靜態總覽。
- `figures/china_provincial_supply_chain_atlas.html`：可點選 31 個省級標記的互動地圖（開啟時需網路載入 OSM/Leaflet）。
- `figures/fig_5_china_coastal_theater_context.svg`：分離的戰區級沿海態勢概覽，不含部隊或基地。
- `figures/gen_figures.py`：檢查 SVG 與輸出 PNG 預覽的可重現腳本。
- `figures/gen_osm_world_map.py`：依 OSMF 使用規範取得低縮放世界底圖、保留七日快取並重建圖 1。需使用工作區所附的 Pillow 環境。
- `figures/gen_china_atlases.py`：依相同 OSMF 規範重建省級與戰區級地圖。

## 使用原則

本研究旨在支援民防、公共政策、供應鏈與關鍵服務持續運作。圖中的「暴露」指外部中斷、制裁、封鎖風險或市場衝擊下的系統壓力，不代表軍事目標價值。

資料檢索截止日：2026-08-13（Asia/Taipei）。

地圖底圖：© OpenStreetMap contributors，資料採 [ODbL](https://www.openstreetmap.org/copyright)；各地圖內亦保留可見署名。
