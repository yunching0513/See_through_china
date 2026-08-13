# 臺海衝突下的戰略依賴與國家韌性研究（非作戰化版本）

本工作區收錄一份以公開資料為基礎的初版政策研究。經濟資料可細分至省級行政區，但不細分至設施；軍事資訊僅到戰區級責任方向且與基礎設施分圖呈現。不包含設施座標、部隊部署、武力打擊點、攻擊排序、癱瘓方法或損害最佳化。

## 互動網站

- index.html：完整互動式研究網站，可直接由 GitHub Pages 部署。
- assets/data.js：由三份已審查 CSV 產生的靜態資料包。
- assets/app.js：省級搜尋／篩選／比較、韌性時間尺度切換及公開脈絡互動。
- assets/vendor/leaflet/：Leaflet 1.9.4 的本地副本，與 unpkg 發布檔 byte 相同（leaflet.js 的 SRI 為 sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=）。網站不再從 CDN 載入程式碼，只有 OSM 圖磚與 Google Fonts 需要網路。
- assets/og-image.png：社群分享縮圖，由 figures/gen_og_image.py 產生。
- scripts/build_web_data.py：重新產生網站資料包；CSV 更新後執行 python3 scripts/build_web_data.py。

本機可直接開啟 index.html，或在工作區執行 python3 -m http.server 8000 後瀏覽 http://localhost:8000。

### 韌性比較圖的配對規則

網站以 `dependency_assessment.csv` 的 `domain` 欄位配對中國與臺灣兩側，不使用列順序。兩側都有同名 domain 才畫成並列對照；只有單邊存在的 domain 會標示「僅有中國資料」或「僅有臺灣資料」，另一側畫成斜線底，並在圖表下方列出原因。

目前金融領域屬於後者：中國側記錄的是「金融與地方債」，臺灣側記錄的是「金融與支付」。兩者衡量的不是同一件事，因此不合併成同一條對照。

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
- `figures/gen_og_image.py`：重建社群分享縮圖 `assets/og-image.png`。腳本會先驗證字型是否涵蓋所需的繁體字，缺字時直接報錯而不是靜默漏字。

## 使用原則

本研究旨在支援民防、公共政策、供應鏈與關鍵服務持續運作。圖中的「暴露」指外部中斷、制裁、封鎖風險或市場衝擊下的系統壓力，不代表軍事目標價值。

資料檢索截止日：2026-08-13（Asia/Taipei）。

地圖底圖：© OpenStreetMap contributors，資料採 [ODbL](https://www.openstreetmap.org/copyright)；各地圖內亦保留可見署名。

## 授權

本專案分兩部分授權：

- 程式碼（`assets/app.js`、`assets/styles.css`、`scripts/`、`figures/*.py`）採 MIT，見 [LICENSE](LICENSE)。
- 研究內容與資料（`report/`、`research_notes/`、`data/`、`figures/` 的 SVG 與 PNG、`README.md`、`RESPONSIBLE_USE.md`）採 [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，見 [LICENSE-CONTENT](LICENSE-CONTENT)。
- OpenStreetMap 圖磚與底圖幾何為 © OpenStreetMap contributors，採 ODbL，不在 CC BY 4.0 範圍內。重用含 OSM 底圖的圖表時請保留可見署名。
- `assets/vendor/leaflet/` 為 Leaflet 1.9.4，採 BSD 2-Clause，授權條款隨附於該目錄。

引用時請一併保留資料檢索截止日，因為各項評估都繫於該日期取得的來源。
