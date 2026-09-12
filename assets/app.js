(() => {
  "use strict";

  const data = window.ATLAS_DATA;
  if (!data) {
    document.body.insertAdjacentHTML("afterbegin", '<p class="load-error">資料載入失敗，請重新整理頁面。</p>');
    return;
  }

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const escapeHTML = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const provinceByName = new Map(data.provinces.map((province) => [province.province, province]));
  const state = { region: "全部", role: "全部", query: "", selected: null, comparison: [] };
  let map = null;
  let mapResizeFrame = 0;
  const markers = new Map();
  const initialBounds = [[17.4, 73], [53.8, 134.8]];

  function shortName(name) {
    return name.replace("壯族自治區", "").replace("維吾爾自治區", "")
      .replace("回族自治區", "").replace("自治區", "")
      .replace("省", "").replace("市", "");
  }

  function initMap() {
    if (!window.L) {
      $("#map-fallback").hidden = false;
      return;
    }
    map = L.map("atlas-map", {
      zoomControl: true, minZoom: 3, maxZoom: 7, attributionControl: false, zoomSnap: .25
    });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 7, attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    data.provinces.forEach((province) => {
      const icon = L.divIcon({
        className: "",
        html: '<div class="atlas-marker" style="--marker-color:' + province.color + '"><span>' + escapeHTML(province.abbr) + "</span></div>",
        iconSize: [29, 29], iconAnchor: [14, 28], tooltipAnchor: [0, -26]
      });
      const marker = L.marker([province.lat, province.lon], { icon, keyboard: true })
        .bindTooltip(
          "<strong>" + escapeHTML(province.province) + "</strong><br>" + escapeHTML(province.role_group),
          { className: "atlas-tooltip", direction: "top", offset: [0, -4] }
        )
        .on("click", () => selectProvince(province.province, false))
        .addTo(map);
      markers.set(province.province, marker);
    });

    const syncMapSize = () => {
      window.cancelAnimationFrame(mapResizeFrame);
      mapResizeFrame = window.requestAnimationFrame(() => {
        map.invalidateSize({ pan: false, debounceMoveend: true });
      });
    };
    const fitInitialView = () => {
      map.invalidateSize({ pan: false });
      map.fitBounds(initialBounds, { animate: false, padding: [18, 18] });
    };

    if ("ResizeObserver" in window) {
      const mapResizeObserver = new ResizeObserver(syncMapSize);
      mapResizeObserver.observe($("#atlas-map"));
    } else {
      window.addEventListener("resize", syncMapSize, { passive: true });
    }
    window.requestAnimationFrame(() => window.requestAnimationFrame(fitInitialView));
    document.fonts?.ready.then(fitInitialView);
  }

  function renderRoleFilters() {
    const roles = [...new Set(data.provinces.map((province) => province.role_group))];
    const counts = Object.fromEntries(roles.map((role) => [
      role, data.provinces.filter((province) => province.role_group === role).length
    ]));
    $("#role-filters").innerHTML = [
      '<button type="button" class="role-filter active" data-role="全部" style="--role-color:#172640">' +
      "<span>全部角色</span><small>" + data.provinces.length + "</small></button>",
      ...roles.map((role) =>
        '<button type="button" class="role-filter" data-role="' + escapeHTML(role) + '" style="--role-color:' + data.roleColors[role] + '">' +
        "<span>" + escapeHTML(role) + "</span><small>" + counts[role] + "</small></button>"
      )
    ].join("");

    $("#map-legend").innerHTML = roles.map((role) =>
      '<span class="legend-item" style="--legend-color:' + data.roleColors[role] + '"><i></i>' + escapeHTML(role) + "</span>"
    ).join("");

    $$("#role-filters .role-filter").forEach((button) => {
      button.addEventListener("click", () => {
        state.role = button.dataset.role;
        $$("#role-filters .role-filter").forEach((candidate) => candidate.classList.toggle("active", candidate === button));
        applyFilters();
      });
    });
  }

  function renderProvinceDirectory() {
    $("#province-list").innerHTML = data.provinces.map((province) =>
      '<button type="button" class="province-item" data-province="' + escapeHTML(province.province) + '" ' +
      'style="--province-color:' + province.color + '">' + escapeHTML(shortName(province.province)) + "</button>"
    ).join("");
    $$(".province-item").forEach((button) => {
      button.addEventListener("click", () => selectProvince(button.dataset.province, true));
    });
  }

  function matchesFilters(province) {
    const query = state.query.trim().toLocaleLowerCase("zh-Hant");
    const searchable = Object.values(province).join(" ").toLocaleLowerCase("zh-Hant");
    return (state.region === "全部" || province.nbs_region === state.region)
      && (state.role === "全部" || province.role_group === state.role)
      && (!query || searchable.includes(query));
  }

  function filteredProvinces() {
    return data.provinces.filter(matchesFilters);
  }

  function applyFilters() {
    const visible = filteredProvinces();
    const visibleNames = new Set(visible.map((province) => province.province));
    markers.forEach((marker, name) => {
      if (!map) return;
      if (visibleNames.has(name) && !map.hasLayer(marker)) marker.addTo(map);
      if (!visibleNames.has(name) && map.hasLayer(marker)) marker.removeFrom(map);
    });
    $$(".province-item").forEach((button) => {
      button.classList.toggle("filtered-out", !visibleNames.has(button.dataset.province));
    });
    $("#result-count").textContent = visible.length + " / " + data.provinces.length;
    $("#map-status").textContent = visible.length === data.provinces.length
      ? "顯示全部省級行政區"
      : "目前顯示 " + visible.length + " 個結果";
  }

  function selectProvince(name, focusMap = true) {
    const province = provinceByName.get(name);
    if (!province) return;
    state.selected = name;
    $("#panel-empty").hidden = true;
    $("#province-detail").hidden = false;
    $("#detail-meta").textContent = province.nbs_region + " · " + province.role_group;
    $("#detail-title").textContent = province.province;
    $("#detail-abbr").textContent = province.abbr;
    $("#detail-function").textContent = province.public_function;
    $("#detail-infra").textContent = province.infrastructure_types;
    $("#detail-products").textContent = province.representative_products_and_clusters;
    $("#detail-upstream").textContent = province.major_upstream_inputs;
    $("#detail-downstream").textContent = province.main_downstream_links;
    $("#detail-confidence").textContent = "資料信心：" + province.confidence;

    markers.forEach((marker, markerName) => {
      marker.getElement()?.querySelector(".atlas-marker")?.classList.toggle("selected", markerName === name);
    });
    $$(".province-item").forEach((button) => {
      button.classList.toggle("active", button.dataset.province === name);
    });
    const addButton = $("#compare-add");
    const included = state.comparison.includes(name);
    addButton.textContent = included ? "已加入比較" : "加入比較";
    addButton.classList.toggle("added", included);
    addButton.disabled = included;

    if (focusMap && map) {
      if (!map.hasLayer(markers.get(name))) {
        Object.assign(state, { region: "全部", role: "全部", query: "" });
        resetFilterControls();
        applyFilters();
      }
      map.flyTo([province.lat, province.lon], Math.max(map.getZoom(), 4.8), { duration: .7 });
      document.querySelector(".atlas-shell").scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  function resetFilterControls() {
    $("#province-search").value = "";
    $$("#region-filters .filter-chip").forEach((button) => {
      const active = button.dataset.region === "全部";
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    $$("#role-filters .role-filter").forEach((button) => {
      button.classList.toggle("active", button.dataset.role === "全部");
    });
  }

  function renderComparison() {
    const drawer = $("#compare-drawer");
    drawer.hidden = state.comparison.length === 0;
    $("#compare-grid").innerHTML = state.comparison.map((name) => {
      const province = provinceByName.get(name);
      return '<article class="compare-card" style="--card-color:' + province.color + '">' +
        '<button class="remove" type="button" data-remove="' + escapeHTML(name) + '" aria-label="從比較移除 ' + escapeHTML(name) + '">×</button>' +
        "<span>" + escapeHTML(province.nbs_region) + " · " + escapeHTML(province.role_group) + "</span>" +
        "<h4>" + escapeHTML(province.province) + "</h4><dl>" +
        "<dt>功能</dt><dd>" + escapeHTML(province.public_function) + "</dd>" +
        "<dt>代表產品</dt><dd>" + escapeHTML(province.representative_products_and_clusters) + "</dd>" +
        "<dt>上游投入</dt><dd>" + escapeHTML(province.major_upstream_inputs) + "</dd></dl></article>";
    }).join("");
    $$("#compare-grid [data-remove]").forEach((button) => {
      button.addEventListener("click", () => {
        state.comparison = state.comparison.filter((name) => name !== button.dataset.remove);
        renderComparison();
        if (state.selected) selectProvince(state.selected, false);
      });
    });
  }

  function initFilters() {
    $("#province-search").addEventListener("input", (event) => {
      state.query = event.target.value;
      applyFilters();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
        event.preventDefault();
        $("#province-search").focus();
      }
    });
    $$("#region-filters .filter-chip").forEach((button) => {
      button.addEventListener("click", () => {
        state.region = button.dataset.region;
        $$("#region-filters .filter-chip").forEach((candidate) => {
          const active = candidate === button;
          candidate.classList.toggle("active", active);
          candidate.setAttribute("aria-pressed", String(active));
        });
        applyFilters();
      });
    });
    $("#reset-filters").addEventListener("click", () => {
      Object.assign(state, { region: "全部", role: "全部", query: "" });
      resetFilterControls();
      applyFilters();
      if (map) map.fitBounds(initialBounds);
    });
    $("#fit-map").addEventListener("click", () => {
      if (!map) return;
      const visible = filteredProvinces();
      if (visible.length === 0) return;
      map.fitBounds(visible.map((province) => [province.lat, province.lon]), { padding: [30, 30], maxZoom: 5.5 });
    });
    $("#compare-add").addEventListener("click", () => {
      if (!state.selected || state.comparison.includes(state.selected)) return;
      if (state.comparison.length >= 3) {
        $("#map-status").textContent = "比較上限為三個省份，請先移除一項";
        return;
      }
      state.comparison.push(state.selected);
      renderComparison();
      selectProvince(state.selected, false);
    });
    $("#clear-compare").addEventListener("click", () => {
      state.comparison = [];
      renderComparison();
      if (state.selected) selectProvince(state.selected, false);
    });
  }

  const LEVEL_SCORES = { "低": 1, "低中": 1.5, "中": 2.25, "中高": 3.25, "高": 4.1, "極高": 5 };
  const LEVEL_MAX = 5;
  const SIDES = { china: "中國", taiwan: "臺灣" };
  let horizon = "acute_0_30d";
  let activeDomain = null;

  function levelWidth(level) {
    const score = LEVEL_SCORES[level];
    if (score === undefined) {
      console.warn("dependency_assessment 出現未定義的等級標記：" + level);
      return 0;
    }
    return score / LEVEL_MAX * 100;
  }

  // 以 domain 欄位配對兩側資料。不使用列順序，避免 CSV 重排或新增列時靜默錯位。
  // 只有單邊存在的 domain 不並列成對照，改以單邊列呈現。
  function groupedDependencies() {
    const bySide = new Map(Object.values(SIDES).map((side) => [side, new Map()]));
    data.dependencies.forEach((row) => {
      const sideRows = bySide.get(row.side);
      if (!sideRows) {
        console.warn("dependency_assessment 出現未定義的 side：" + row.side);
        return;
      }
      sideRows.set(row.domain, row);
    });
    const entries = [...new Set(data.dependencies.map((row) => row.domain))].map((domain) => ({
      domain,
      china: bySide.get(SIDES.china).get(domain) ?? null,
      taiwan: bySide.get(SIDES.taiwan).get(domain) ?? null
    }));
    return [
      ...entries.filter((entry) => entry.china && entry.taiwan),
      ...entries.filter((entry) => !entry.china || !entry.taiwan)
    ];
  }

  function renderResilienceChart() {
    const entries = groupedDependencies();
    const bar = (row, side) => row
      ? '<span class="bar-track"><span class="bar ' + side + '" style="width:' + levelWidth(row[horizon]) + '%"></span></span>'
      : '<span class="bar-track empty"></span>';

    $("#resilience-chart").innerHTML = entries.map(({ domain, china, taiwan }) => {
      const paired = Boolean(china && taiwan);
      const onlySide = china ? SIDES.china : SIDES.taiwan;
      return '<button class="domain-row' + (domain === activeDomain ? " active" : "") +
        (paired ? "" : " unpaired") + '" type="button" data-domain="' + escapeHTML(domain) + '"' +
        ' aria-pressed="' + String(domain === activeDomain) + '">' +
        '<span class="domain-name">' + escapeHTML(domain) +
        (paired ? "" : "<small>僅有" + escapeHTML(onlySide) + "資料</small>") + "</span>" +
        '<span class="bar-pair">' + bar(china, "china") + bar(taiwan, "taiwan") + "</span>" +
        '<span class="domain-values">' + escapeHTML(china ? china[horizon] : "—") +
        " / " + escapeHTML(taiwan ? taiwan[horizon] : "—") + "</span></button>";
    }).join("");

    const unpaired = entries.filter((entry) => !entry.china || !entry.taiwan);
    const note = $("#chart-note");
    note.hidden = unpaired.length === 0;
    note.textContent = unpaired.length === 0 ? "" :
      "最後 " + unpaired.length + " 個領域只有單邊資料：" + unpaired.map((entry) => entry.domain).join("、") +
      "。資料集沒有另一側的同名領域，因此網站不把它們合併成同一條對照。";

    $$(".domain-row").forEach((button) => {
      button.addEventListener("click", () => {
        activeDomain = button.dataset.domain;
        renderResilienceChart();
        renderInsight();
      });
    });
  }

  function renderInsight() {
    const entry = groupedDependencies().find((item) => item.domain === activeDomain);
    if (!entry) return;
    const { domain, china, taiwan } = entry;
    const paired = Boolean(china && taiwan);
    const sideBlock = (row, label, cls) => row
      ? '<div class="insight-side ' + cls + '"><strong>' + escapeHTML(label) + ' <span>' + escapeHTML(row[horizon]) + "</span></strong>" +
        "<p>" + escapeHTML(row.interpretation_note) + "</p><p><small>依據：" + escapeHTML(row.evidence_basis) + "</small></p></div>"
      : '<div class="insight-side empty"><strong>' + escapeHTML(label) + " <span>無對應資料</span></strong>" +
        "<p>資料集沒有這一側的同名領域。這一列只呈現單邊觀察，不能讀成兩岸對照。</p></div>";
    $("#chart-insight").innerHTML =
      '<p class="insight-label">EVIDENCE NOTE · ' + (paired ? "可比對領域" : "單邊領域") + "</p>" +
      "<h3>" + escapeHTML(domain) + "</h3>" +
      sideBlock(china, SIDES.china, "china") + sideBlock(taiwan, SIDES.taiwan, "taiwan");
  }

  function initResilience() {
    activeDomain = groupedDependencies()[0]?.domain ?? null;
    $$(".horizon-switch button").forEach((button) => {
      button.addEventListener("click", () => {
        horizon = button.dataset.horizon;
        $$(".horizon-switch button").forEach((candidate) => {
          const active = candidate === button;
          candidate.classList.toggle("active", active);
          candidate.setAttribute("aria-pressed", String(active));
        });
        renderResilienceChart();
        renderInsight();
      });
    });
    renderResilienceChart();
    renderInsight();
  }

  function renderTheaters() {
    const colors = ["#4f84c4", "#db3a34", "#16866c"];
    $("#theater-list").innerHTML = data.theaters.map((theater, index) =>
      '<article class="theater-card" style="--theater-color:' + colors[index] + '">' +
      "<span>" + escapeHTML(theater.coastal_macro_area) + "</span><h3>" + escapeHTML(theater.theater_level) + "</h3>" +
      "<p>" + escapeHTML(theater.public_role) + '</p><details><summary>查看公開活動型態與排除項目</summary><dl>' +
      "<dt>公開活動型態</dt><dd>" + escapeHTML(theater.public_activity_patterns) + "</dd>" +
      "<dt>明確排除</dt><dd>" + escapeHTML(theater.detail_excluded) + "</dd></dl></details></article>"
    ).join("");
  }

  function renderSourceCoverage() {
    const coverage = data.sourceCoverage || [];
    const maximum = Math.max(...coverage.map((row) => Number(row.record_count)), 1);
    $("#source-coverage-chart").innerHTML = coverage.map((row) => {
      const count = Number(row.record_count);
      const width = Math.max(4, count / maximum * 100);
      return '<div class="coverage-row" title="' + escapeHTML(row.interpretation_note) + '">' +
        '<div class="coverage-label"><span>' + escapeHTML(row.category) + '</span><strong>' +
        count.toLocaleString("zh-TW") + '</strong></div>' +
        '<div class="coverage-track"><span style="width:' + width + '%"></span></div>' +
        '<small>' + escapeHTML(row.source_layer_count) + ' 個原圖層</small></div>';
    }).join("");
  }

  // 首頁摘要數字一律由資料推導，避免 HTML 的靜態值與 CSV 不同步。
  function renderSummaryMetrics() {
    const set = (selector, value) => {
      const node = $(selector);
      if (node) node.textContent = String(value);
    };
    const distinct = (key) => new Set(data.provinces.map((province) => province[key])).size;
    set("#metric-provinces", data.provinces.length);
    set("#metric-roles", distinct("role_group"));
    set("#metric-regions", distinct("nbs_region"));
    set("#metric-domains", groupedDependencies().filter((entry) => entry.china && entry.taiwan).length);
    set("#panel-count", data.provinces.length);
  }

  renderSummaryMetrics();
  renderRoleFilters();
  renderProvinceDirectory();
  initMap();
  initFilters();
  initResilience();
  renderTheaters();
  renderSourceCoverage();
  applyFilters();
})();
