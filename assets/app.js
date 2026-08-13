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
      '<button type="button" class="role-filter active" data-role="全部" style="--role-color:#172640"><span>全部角色</span><small>31</small></button>',
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
    $("#result-count").textContent = visible.length + " / 31";
    $("#map-status").textContent = visible.length === 31
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

  const levelScore = { "低": 1, "低中": 1.5, "中": 2.25, "中高": 3.25, "高": 4.1, "極高": 5 };
  let horizon = "acute_0_30d";
  const comparisonDomains = [
    "能源與燃料", "糧食與飼料", "外貿與製造需求", "金融系統",
    "先進科技投入", "海運與跨境物流", "數位與跨境資料"
  ];
  let activeDomain = comparisonDomains[0];

  function groupedDependencies() {
    const chinaRows = data.dependencies.filter((row) => row.side === "中國");
    const taiwanRows = data.dependencies.filter((row) => row.side === "臺灣");
    return comparisonDomains.map((domain, index) => ({
      domain,
      china: chinaRows[index],
      taiwan: taiwanRows[index]
    }));
  }

  function renderResilienceChart() {
    $("#resilience-chart").innerHTML = groupedDependencies().map(({ domain, china, taiwan }) => {
      const chinaValue = china[horizon];
      const taiwanValue = taiwan[horizon];
      return '<button class="domain-row ' + (domain === activeDomain ? "active" : "") + '" type="button" data-domain="' + escapeHTML(domain) + '">' +
        '<span class="domain-name">' + escapeHTML(domain) + '</span><span class="bar-pair">' +
        '<span class="bar-track"><span class="bar china" style="width:' + (levelScore[chinaValue] / 5 * 100) + '%"></span></span>' +
        '<span class="bar-track"><span class="bar taiwan" style="width:' + (levelScore[taiwanValue] / 5 * 100) + '%"></span></span></span>' +
        '<span class="domain-values">' + escapeHTML(chinaValue) + " / " + escapeHTML(taiwanValue) + "</span></button>";
    }).join("");
    $$(".domain-row").forEach((button) => {
      button.addEventListener("click", () => {
        activeDomain = button.dataset.domain;
        renderResilienceChart();
        renderInsight();
      });
    });
  }

  function renderInsight() {
    const { china, taiwan } = groupedDependencies().find((item) => item.domain === activeDomain);
    $("#chart-insight").innerHTML =
      '<p class="insight-label">EVIDENCE NOTE · ' + escapeHTML(activeDomain) + "</p><h3>" + escapeHTML(activeDomain) + "</h3>" +
      '<div class="insight-side china"><strong>中國 <span>' + escapeHTML(china[horizon]) + "</span></strong>" +
      "<p>" + escapeHTML(china.interpretation_note) + "</p><p><small>依據：" + escapeHTML(china.evidence_basis) + "</small></p></div>" +
      '<div class="insight-side"><strong>臺灣 <span>' + escapeHTML(taiwan[horizon]) + "</span></strong>" +
      "<p>" + escapeHTML(taiwan.interpretation_note) + "</p><p><small>依據：" + escapeHTML(taiwan.evidence_basis) + "</small></p></div>";
  }

  function initResilience() {
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

  renderRoleFilters();
  renderProvinceDirectory();
  initMap();
  initFilters();
  initResilience();
  renderTheaters();
  applyFilters();
})();
