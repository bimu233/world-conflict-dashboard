<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';
  import { geoNameToCSV } from './lib/nameMap.js';

  import WorldMap           from './lib/Map.svelte';
  import ConflictPanel      from './lib/ConflictPanel.svelte';
  import SourceClarityPanel from './lib/SourceClarityPanel.svelte';
  import TradePanel         from './lib/TradePanel.svelte';
  import TimeSeriesChart    from './lib/TimeSeriesChart.svelte';
  import RegionBarChart     from './lib/RegionBarChart.svelte';
  import CountryRankChart   from './lib/CountryRankChart.svelte';
  import TradeTrendChart        from './lib/TradeTrendChart.svelte';
  import TradePartnersChart     from './lib/TradePartnersChart.svelte';
  import TradeBalanceChart      from './lib/TradeBalanceChart.svelte';
  import TradeConflictChart     from './lib/TradeConflictChart.svelte';
  import TradeConflictPanel        from './lib/TradeConflictPanel.svelte';
  import TradeDistributionChart    from './lib/TradeDistributionChart.svelte';
  import EconomyTrendChart         from './lib/EconomyTrendChart.svelte';
  import EconomyRankChart          from './lib/EconomyRankChart.svelte';
  import EconomyPanel              from './lib/EconomyPanel.svelte';
  import EconomyScatterChart       from './lib/EconomyScatterChart.svelte';
  import ConflictTradeScatter      from './lib/ConflictTradeScatter.svelte';

  // ── data ──────────────────────────────────────────────────────────────────
  let geoData          = null;
  let mapData          = [];   // [{year, country, region, deaths}]
  let allConflicts     = [];   // [{year, country, region, conflict_name, side_a, side_b, deaths_a, deaths_b, best}]
  let tradeFlows       = {};   // { "ISO3_YEAR": [{partner_iso3, total_usd, ...}] }
  let worldTradeTotals = {};   // { "ISO3": [{year, exports_usd, imports_usd}] }
  let wdiData          = {};   // { "ISO3": [{year, gdp_growth, fdi_pct_gdp, trade_pct_gdp}] }

  onMount(async () => {
    const [conflicts, totals, geo, flows, worldTotals, wdi] = await Promise.all([
      d3.json('/data/conflicts.json'),
      d3.json('/data/map_data.json'),
      d3.json('/data/custom.geojson'),
      d3.json('/data/trade_flows.json'),
      d3.json('/data/world_trade_totals.json'),
      d3.json('/data/wdi_indicators.json'),
    ]);
    geoData          = geo;
    allConflicts     = conflicts;
    mapData          = totals;
    tradeFlows       = flows        ?? {};
    worldTradeTotals = worldTotals  ?? {};
    wdiData          = wdi          ?? {};
  });

  // ── view mode ─────────────────────────────────────────────────────────────
  let viewMode = 'conflict'; // 'conflict' | 'trade' | 'relation' | 'economy'

  // ── cross-filter state ────────────────────────────────────────────────────
  let selectedYear    = 2010;
  let selectedCountry = "Mexico";
  let selectedRegion  = "Americas";

  // ── conflict panel sub-view ───────────────────────────────────────────────
  let conflictPanelView = 'events'; // 'events' | 'clarity'

  // ── ISO3 / name lookups from GeoJSON ──────────────────────────────────────
  $: iso3ByCSVName = geoData
    ? new Map(
        geoData.features
          .filter(f => f.properties.iso_a3 && f.properties.iso_a3 !== '-99')
          .map(f => [geoNameToCSV(f.properties.name), f.properties.iso_a3])
      )
    : new Map();

  $: nameByISO3 = geoData
    ? new Map(
        geoData.features
          .filter(f => f.properties.iso_a3 && f.properties.iso_a3 !== '-99')
          .map(f => [f.properties.iso_a3, f.properties.name])
      )
    : new Map();

  $: selectedISO3 = selectedCountry ? (iso3ByCSVName.get(selectedCountry) ?? null) : null;

  // ── trade partners for selected country-year ──────────────────────────────
  $: tradePartners = (() => {
    if (!selectedISO3 || !selectedYear || !tradeFlows) return [];
    const flows = tradeFlows[`${selectedISO3}_${selectedYear}`] ?? [];
    return flows.map(f => ({
      ...f,
      partner_name: nameByISO3.get(f.partner_iso3) ?? f.partner_iso3,
    }));
  })();

  // ── world total for selected country-year (for TradePanel summary row) ────
  $: selectedWorldTotal = (() => {
    if (!selectedISO3 || !worldTradeTotals[selectedISO3]) return null;
    return worldTradeTotals[selectedISO3].find(d => d.year === selectedYear) ?? null;
  })();

  // ── trade trend series for selected country (all years) ───────────────────
  $: tradeTrendData = selectedISO3 ? (worldTradeTotals[selectedISO3] ?? []) : [];

  // ── map data ──────────────────────────────────────────────────────────────
  $: filteredData = mapData.filter(d => d.year === selectedYear);

  // ── conflict view derived data ────────────────────────────────────────────
  $: panelConflicts = selectedCountry
    ? allConflicts.filter(c => c.year === selectedYear && c.country === selectedCountry)
    : [];

  $: timeSeriesData = (() => {
    let rows = allConflicts;
    if (selectedCountry) rows = rows.filter(c => c.country === selectedCountry);
    if (selectedRegion)  rows = rows.filter(c => c.region  === selectedRegion);
    const byYear = new Map();
    rows.forEach(c => {
      const cur = byYear.get(c.year) || { deaths: 0, low: 0, high: 0 };
      byYear.set(c.year, {
        deaths: cur.deaths + c.best,
        low:    cur.low   + (c.low  ?? c.best),
        high:   cur.high  + (c.high ?? c.best),
      });
    });
    return [...byYear.entries()]
      .map(([year, v]) => ({ year, deaths: v.deaths, low: v.low, high: v.high }))
      .sort((a, b) => a.year - b.year);
  })();

  $: timeSeriesLabel = [
    selectedCountry && selectedCountry,
    selectedRegion  && selectedRegion,
  ].filter(Boolean).join(' · ');

  $: regionData = (() => {
    const rows = allConflicts.filter(c => c.year === selectedYear);
    const byRegion = new Map();
    rows.forEach(c => byRegion.set(c.region, (byRegion.get(c.region) || 0) + c.best));
    return [...byRegion.entries()]
      .map(([region, deaths]) => ({ region, deaths }))
      .sort((a, b) => b.deaths - a.deaths);
  })();

  $: countryRankData = (() => {
    let rows = allConflicts.filter(c => c.year === selectedYear);
    if (selectedRegion) rows = rows.filter(c => c.region === selectedRegion);
    const byCountry = new Map();
    rows.forEach(c => byCountry.set(c.country, (byCountry.get(c.country) || 0) + c.best));
    return [...byCountry.entries()]
      .map(([country, deaths]) => ({ country, deaths }))
      .sort((a, b) => b.deaths - a.deaths)
      .slice(0, 10);
  })();

  // ── relation view: ISO3 → CSV name (reverse of iso3ByCSVName) ────────────
  $: csvNameByISO3 = geoData
    ? new Map(
        geoData.features
          .filter(f => f.properties.iso_a3 && f.properties.iso_a3 !== '-99')
          .map(f => [f.properties.iso_a3, geoNameToCSV(f.properties.name)])
      )
    : new Map();

  // ── relation view: per-year deaths + trade % change for selected country ──
  $: tradeConflictSeries = (() => {
    if (!selectedISO3) return [];
    const tradeSeries = worldTradeTotals[selectedISO3] ?? [];
    // deaths by year for this country
    const csvName = csvNameByISO3.get(selectedISO3);
    const deathsByYear = new Map();
    allConflicts
      .filter(c => c.country === csvName)
      .forEach(c => deathsByYear.set(c.year, (deathsByYear.get(c.year) || 0) + c.best));

    // compute trade % change year-over-year
    const tradeByYear = new Map(tradeSeries.map(d => [d.year, (d.exports_usd ?? 0) + (d.imports_usd ?? 0)]));
    const years = [...tradeByYear.keys()].sort((a, b) => a - b);
    const tradePctByYear = new Map();
    years.forEach((yr, i) => {
      if (i === 0) return;
      const prev = tradeByYear.get(years[i - 1]);
      const cur  = tradeByYear.get(yr);
      if (prev && prev > 0) tradePctByYear.set(yr, ((cur - prev) / prev) * 100);
    });

    // union of years
    const allYrs = [...new Set([...deathsByYear.keys(), ...tradePctByYear.keys()])].sort((a, b) => a - b);
    return allYrs.map(yr => ({
      year:     yr,
      deaths:   deathsByYear.get(yr) ?? null,
      tradePct: tradePctByYear.get(yr) ?? null,
    }));
  })();


  // ── relation view: trade % change for all countries in selected year ─────
  $: yearTradePcts = (() => {
    const result = [];
    for (const [iso3, tradeSeries] of Object.entries(worldTradeTotals)) {
      const cur  = tradeSeries.find(d => d.year === selectedYear);
      const prev = tradeSeries.find(d => d.year === selectedYear - 1);
      if (!cur || !prev) continue;
      const curV  = (cur.exports_usd  ?? 0) + (cur.imports_usd  ?? 0);
      const prevV = (prev.exports_usd ?? 0) + (prev.imports_usd ?? 0);
      if (prevV <= 0) continue;
      result.push({ iso3, country: csvNameByISO3.get(iso3) ?? iso3, tradePct: ((curV - prevV) / prevV) * 100 });
    }
    return result;
  })();

  $: selectedYearTradePct = selectedISO3
    ? (yearTradePcts.find(d => d.iso3 === selectedISO3)?.tradePct ?? null)
    : null;

  // ── relation view: GDP growth for all countries in selected year ──────────
  $: yearGdpPcts = (() => {
    const result = [];
    for (const [iso3, series] of Object.entries(wdiData)) {
      if (iso3.length !== 3) continue;
      const row = series.find(d => d.year === selectedYear);
      if (row?.gdp_growth == null) continue;
      result.push({ iso3, country: csvNameByISO3.get(iso3) ?? iso3, gdpGrowth: row.gdp_growth });
    }
    return result;
  })();

  $: selectedYearGdp = selectedISO3
    ? (yearGdpPcts.find(d => d.iso3 === selectedISO3)?.gdpGrowth ?? null)
    : null;

  // ── relation view: deaths + GDP growth per year for selected country ──────
  $: tradeConflictGdpSeries = (() => {
    if (!selectedISO3) return [];
    const wdiSeries = wdiData[selectedISO3] ?? [];
    const csvName   = csvNameByISO3.get(selectedISO3);
    const deathsByYear = new Map();
    allConflicts.filter(c => c.country === csvName)
                .forEach(c => deathsByYear.set(c.year, (deathsByYear.get(c.year) || 0) + c.best));
    const allYrs = [...new Set([...deathsByYear.keys(), ...wdiSeries.map(d => d.year)])].sort((a, b) => a - b);
    return allYrs.map(yr => ({
      year:      yr,
      deaths:    deathsByYear.get(yr) ?? null,
      gdpGrowth: wdiSeries.find(d => d.year === yr)?.gdp_growth ?? null,
    }));
  })();

  // ── relation view: deaths + trade % change for all countries in selected year ──
  $: conflictTradeScatterData = (() => {
    const deathMap = new Map(
      mapData
        .filter(d => d.year === selectedYear)
        .map(d => [d.country, d.deaths])
    );
    return yearTradePcts
      .map(d => ({ ...d, deaths: deathMap.get(d.country) ?? 0 }))
      .filter(d => d.deaths != null && d.tradePct != null);
  })();

  // ── economy view ─────────────────────────────────────────────────────────
  $: economySeries = selectedISO3 ? (wdiData[selectedISO3] ?? []) : [];

  $: economyRow     = economySeries.find(d => d.year === selectedYear)     ?? null;
  $: economyPrevRow = economySeries.find(d => d.year === selectedYear - 1) ?? null;

  // top 8 + bottom 8 by GDP growth for selected year (excluding aggregates)
  $: economyRankData = (() => {
    const rows = [];
    for (const [iso3, series] of Object.entries(wdiData)) {
      if (iso3.length !== 3) continue;
      const row = series.find(d => d.year === selectedYear);
      if (!row?.gdp_growth) continue;
      const country = csvNameByISO3.get(iso3) ?? row.country ?? iso3;
      rows.push({ country, iso3, gdp_growth: row.gdp_growth });
    }
    rows.sort((a, b) => b.gdp_growth - a.gdp_growth);
    const top    = rows.slice(0, 8);
    const bottom = rows.slice(-8).reverse();
    // avoid duplicates if total < 16
    const seen = new Set(top.map(d => d.iso3));
    return [...top, ...bottom.filter(d => !seen.has(d.iso3))];
  })();

  // ── economy scatter: all countries' GDP growth + FDI for selected year ───
  $: economyScatterData = (() => {
    const rows = [];
    for (const [iso3, series] of Object.entries(wdiData)) {
      if (iso3.length !== 3) continue;
      const row = series.find(d => d.year === selectedYear);
      if (row?.gdp_growth == null || row?.fdi_pct_gdp == null) continue;
      rows.push({
        iso3,
        country:     csvNameByISO3.get(iso3) ?? row.country ?? iso3,
        gdp_growth:  row.gdp_growth,
        fdi_pct_gdp: row.fdi_pct_gdp,
      });
    }
    return rows;
  })();

  // ── event handlers ────────────────────────────────────────────────────────
  function handleCountryClick(e) {
    const name = e.detail;
    if (selectedCountry === name) {
      selectedCountry = null;
      selectedRegion  = null;
      return;
    }
    conflictPanelView = 'events';
    selectedCountry = name;
    const match = mapData.find(d => d.country === name && d.year === selectedYear);
    if (match) selectedRegion = match.region;
  }

  function handleCountrySelect(e) {
    const name = e.detail;
    if (name !== selectedCountry) conflictPanelView = 'events';
    selectedCountry = name;
    if (!name) { selectedRegion = null; return; }
    const match = mapData.find(d => d.country === name && d.year === selectedYear);
    if (match) selectedRegion = match.region;
  }

  function handleTradePartnerSelect(e) {
    const name = e.detail;
    selectedCountry = name;
  }

  function handleRegionSelect(e) {
    selectedCountry = null;
    selectedRegion = e.detail;
  }

  function handleYearSelect(e) {
    selectedYear = e.detail;
  }
</script>

<h1>Conflict Events Dashboard</h1>

<div class="controls">
  <!-- View toggle -->
  <div class="view-toggle">
    <button
      class="view-btn"
      class:active={viewMode === 'conflict'}
      on:click={() => viewMode = 'conflict'}
    >Conflict View</button>
    <button
      class="view-btn"
      class:active={viewMode === 'trade'}
      on:click={() => viewMode = 'trade'}
    >Trade View</button>
    <button
      class="view-btn"
      class:active={viewMode === 'relation'}
      on:click={() => viewMode = 'relation'}
    >Trade vs Conflict</button>
    <button
      class="view-btn"
      class:active={viewMode === 'economy'}
      on:click={() => viewMode = 'economy'}
    >Economy</button>
  </div>

  <div class="divider"></div>

  <label>Year: <strong>{selectedYear}</strong></label>
  <input type="range" min="1989" max="2024" step="1" bind:value={selectedYear} />

  {#if selectedRegion || selectedCountry}
    <span class="active-filters">
      Filters:
      {#if selectedRegion}
        <button class="chip conflict" on:click={() => selectedRegion = null}>{selectedRegion} ✕</button>
      {/if}
      {#if selectedCountry}
        <button class="chip conflict" on:click={() => selectedCountry = null}>{selectedCountry} ✕</button>
      {/if}
    </span>
  {/if}
</div>

{#if viewMode === 'economy'}
  <!-- ── Economy view: map + trend on left, panel + ranking stacked on right ── -->
  <div class="economy-layout">
    <!-- col 1, row 1: map -->
    <div class="economy-map-cell">
      {#if geoData && mapData.length}
        <WorldMap
          {geoData}
          data={filteredData}
          {selectedCountry}
          {selectedRegion}
          {tradeFlows}
          selectedYear={selectedYear}
          on:countryClick={handleCountryClick}
        />
      {:else}
        <p class="loading">Loading…</p>
      {/if}
    </div>

    <!-- col 2, row 1: panel + ranking stacked, total height = map height -->
    <div class="economy-right">
      <EconomyPanel
        country={selectedCountry ?? ''}
        year={selectedYear}
        row={economyRow}
        prevRow={economyPrevRow}
        on:close={() => selectedCountry = null}
      />
      <div class="economy-rank-fill">
        <EconomyRankChart
          rankData={economyRankData}
          {selectedCountry}
          on:countrySelect={handleCountrySelect}
        />
      </div>
    </div>

    <!-- col 1, row 2: trend chart (same 960px width as map) -->
    <div class="economy-trend-cell">
      <EconomyTrendChart
        series={economySeries}
        {selectedYear}
        filterLabel={selectedCountry ?? ''}
        on:yearSelect={handleYearSelect}
      />
    </div>

    <!-- col 2, row 2: scatter plot, fills same height as trend chart -->
    <div class="economy-scatter-cell">
      <EconomyScatterChart
        data={economyScatterData}
        {selectedCountry}
        year={selectedYear}
        on:countrySelect={handleCountrySelect}
      />
    </div>
  </div>

{:else if viewMode === 'relation'}
  <!-- ── Relation view: two independent flex columns ── -->
  <div class="relation-grid">
    <!-- left column: map on top, charts directly below -->
    <div class="relation-left-col">
      <div class="relation-map-cell">
        {#if geoData && mapData.length}
          <WorldMap
            {geoData}
            data={filteredData}
            {selectedCountry}
            {selectedRegion}
            {tradeFlows}
            selectedYear={selectedYear}
            on:countryClick={handleCountryClick}
          />
        {:else}
          <p class="loading">Loading…</p>
        {/if}
      </div>
      <div class="relation-charts-cell">
        <TradeConflictChart
          series={tradeConflictSeries}
          {selectedYear}
          filterLabel={selectedCountry ?? ''}
          on:yearSelect={handleYearSelect}
        />
        <TradeConflictPanel
          country={selectedCountry ?? ''}
          series={tradeConflictSeries}
          gdpSeries={tradeConflictGdpSeries}
          on:close={() => selectedCountry = null}
        />
      </div>
    </div>

    <!-- right column: distributions on top, scatter below, independent of left -->
    <div class="relation-right-col">
      <div class="relation-dist-cell">
        <TradeDistributionChart
          pcts={yearTradePcts}
          selectedPct={selectedYearTradePct}
          gdpPcts={yearGdpPcts}
          selectedGdpPct={selectedYearGdp}
          {selectedCountry}
          year={selectedYear}
        />
      </div>
      <div class="relation-scatter-cell">
        <ConflictTradeScatter
          data={conflictTradeScatterData}
          {selectedCountry}
          year={selectedYear}
          on:countrySelect={handleCountrySelect}
        />
      </div>
    </div>
  </div>

{:else}
  <!-- ── row 1: map + panel (conflict / trade views) ────────────────────── -->
  <div class="layout-top">
    {#if geoData && mapData.length}
      <WorldMap
        {geoData}
        data={filteredData}
        {selectedCountry}
        {selectedRegion}
        {tradeFlows}
        selectedYear={selectedYear}
        on:countryClick={handleCountryClick}
      />
    {:else}
      <p class="loading">Loading…</p>
    {/if}

    <!-- Conflict panel -->
    {#if viewMode === 'conflict' && selectedCountry}
      {#if panelConflicts.length}
        <div class="conflict-panel-wrap">
          <div class="panel-tabs">
            <button
              class="panel-tab"
              class:active={conflictPanelView === 'events'}
              on:click={() => conflictPanelView = 'events'}
            >Event Table</button>
            <button
              class="panel-tab"
              class:active={conflictPanelView === 'clarity'}
              on:click={() => conflictPanelView = 'clarity'}
            >Source Clarity</button>
          </div>
          {#if conflictPanelView === 'events'}
            <ConflictPanel
              country={selectedCountry}
              year={selectedYear}
              conflicts={panelConflicts}
              on:close={() => selectedCountry = null}
            />
          {:else}
            <SourceClarityPanel
              country={selectedCountry}
              year={selectedYear}
              conflicts={panelConflicts}
              on:close={() => selectedCountry = null}
            />
          {/if}
        </div>
      {:else}
        <div class="no-data">
          <strong>{selectedCountry}</strong> — no conflict data for {selectedYear}
          <button on:click={() => selectedCountry = null}>✕</button>
        </div>
      {/if}
    {/if}

    <!-- Trade panel -->
    {#if viewMode === 'trade' && selectedCountry}
      {#if tradePartners.length || selectedWorldTotal}
        <TradePanel
          country={selectedCountry}
          year={selectedYear}
          {tradePartners}
          worldTotal={selectedWorldTotal}
          on:close={() => selectedCountry = null}
        />
      {:else}
        <div class="no-data">
          <strong>{selectedCountry}</strong> — no trade data for {selectedYear}
          <button on:click={() => selectedCountry = null}>✕</button>
        </div>
      {/if}
    {/if}
  </div>

  <!-- ── row 2: subplots ─────────────────────────────────────────────────── -->
  <div class="layout-charts">
    {#if viewMode === 'conflict' && allConflicts.length}
      <TimeSeriesChart
        yearData={timeSeriesData}
        {selectedYear}
        filterLabel={timeSeriesLabel}
        on:yearSelect={handleYearSelect}
      />
      <RegionBarChart
        {regionData}
        {selectedRegion}
        on:regionSelect={handleRegionSelect}
      />
      <CountryRankChart
        rankData={countryRankData}
        {selectedCountry}
        on:countrySelect={handleCountrySelect}
      />
    {/if}

    {#if viewMode === 'trade'}
      <TradeTrendChart
        trendData={tradeTrendData}
        {selectedYear}
        filterLabel={selectedCountry ?? ''}
        on:yearSelect={handleYearSelect}
      />
      <TradePartnersChart
        {tradePartners}
        {selectedCountry}
        on:countrySelect={handleTradePartnerSelect}
      />
      <TradeBalanceChart
        {tradePartners}
      />
    {/if}
  </div>
{/if}

<style>
  h1 {
    text-align: left;
    padding-left: 16px;
    font-size: 1.8rem;
    margin: 16px 0 4px;
  }

  .controls {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 8px 0 12px 16px;
    font-size: 0.9rem;
  }

  .view-toggle {
    display: flex;
    border: 1px solid #ccc;
    border-radius: 6px;
    overflow: hidden;
  }

  .view-btn {
    padding: 5px 14px;
    font-size: 0.82rem;
    font-weight: 500;
    background: #fff;
    border: none;
    cursor: pointer;
    color: #555;
    transition: background 0.15s, color 0.15s;
  }

  .view-btn:not(:last-child) {
    border-right: 1px solid #ccc;
  }

  .view-btn.active {
    background: #2c3e50;
    color: #fff;
  }

  .view-btn:not(.active):hover {
    background: #f5f5f5;
  }

  .divider {
    width: 1px;
    height: 20px;
    background: #ddd;
  }

  .controls input[type=range] {
    width: 220px;
  }

  .active-filters {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    color: #666;
  }

  .chip {
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.78rem;
    cursor: pointer;
  }

  .chip.conflict {
    background: #fdecea;
    color: #c0392b;
    border: 1px solid #f5b7b1;
  }
  .chip.conflict:hover { background: #f5b7b1; }

  .layout-top {
    display: grid;
    grid-template-columns: 960px 1fr;
    gap: 16px;
    align-items: flex-start;
    padding: 0 0 12px 16px;
  }

  .layout-charts {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 0 16px 32px 16px;
  }

  .loading {
    text-align: center;
    margin: 40px auto;
    color: #888;
  }

  .no-data {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9rem;
    color: #555;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    align-self: flex-start;
  }

  .no-data button {
    margin-left: auto;
    background: none;
    border: none;
    cursor: pointer;
    color: #888;
    font-size: 1rem;
  }

  .conflict-panel-wrap {
    display: flex;
    flex-direction: column;
    gap: 0;
    align-self: flex-start;
    width: 100%;
  }

  .panel-tabs {
    display: flex;
    border: 1px solid #ddd;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    overflow: hidden;
    background: #f5f5f5;
  }

  .panel-tab {
    flex: 1;
    padding: 6px 12px;
    font-size: 0.80rem;
    font-weight: 500;
    background: none;
    border: none;
    border-right: 1px solid #ddd;
    cursor: pointer;
    color: #666;
    transition: background 0.15s, color 0.15s;
  }

  .panel-tab:last-child { border-right: none; }

  .panel-tab.active {
    background: #fff;
    color: #2c3e50;
    font-weight: 600;
  }

  .panel-tab:not(.active):hover { background: #eee; }

  /* make the inner panel connect seamlessly to the tab bar */
  .conflict-panel-wrap :global(.panel) {
    border-top-left-radius: 0;
    border-top-right-radius: 0;
  }

  /* relation view: two independent flex columns so right col height doesn't shift left col */
  .relation-grid {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 0 16px 16px 16px;
  }

  .relation-left-col {
    width: 960px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .relation-right-col {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  /* distributions fills map height explicitly */
  .relation-dist-cell { height: 600px; }

  .relation-charts-cell { display: flex; gap: 16px; align-items: stretch; }
  .relation-scatter-cell { align-self: flex-start; }

  /* economy view: left col has map (row1) + trend (row2); right col spans both rows */
  .economy-layout {
    display: grid;
    grid-template-columns: 960px 1fr;
    grid-template-rows: auto auto;
    column-gap: 16px;
    row-gap: 16px;
    padding: 0 16px 16px 16px;
  }

  .economy-map-cell   { grid-column: 1; grid-row: 1; }
  .economy-trend-cell { grid-column: 1; grid-row: 2; }
  .economy-scatter-cell { grid-column: 2; grid-row: 2; display: flex; }

  /* right column: exactly map height, panel at top, ranking fills remaining */
  .economy-right {
    grid-column: 2;
    grid-row: 1;
    height: 500px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  /* ranking chart fills all remaining height after the panel, scrolls if content overflows */
  .economy-rank-fill {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
  }

</style>
