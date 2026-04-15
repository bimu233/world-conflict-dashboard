<script>
  import { onMount } from 'svelte';
  import * as d3 from 'd3';

  import WorldMap        from './lib/Map.svelte';
  import ConflictPanel   from './lib/ConflictPanel.svelte';
  import TimeSeriesChart from './lib/TimeSeriesChart.svelte';
  import RegionBarChart  from './lib/RegionBarChart.svelte';
  import CountryRankChart from './lib/CountryRankChart.svelte';

  // ── data ──────────────────────────────────────────────────────────────────
  let geoData      = null;
  let mapData      = [];      // [{year, country, region, deaths}]
  let allConflicts = [];      // [{year, country, region, conflict_name, side_a, side_b, deaths_a, deaths_b, best}]

  onMount(async () => {
    const [conflicts, totals, geo] = await Promise.all([
      d3.json('/data/conflicts.json'),
      d3.json('/data/map_data.json'),
      d3.json('/data/custom.geojson'),
    ]);
    geoData      = geo;
    allConflicts = conflicts;
    mapData      = totals;
  });

  // ── cross-filter state ────────────────────────────────────────────────────
  let selectedYear    = 2010;
  let selectedCountry = "Mexico";   // CSV country name
  let selectedRegion  = "Americas";   // one of Africa / Americas / Asia / Europe / Middle East

  // ── map (choropleth) ──────────────────────────────────────────────────────
  // Pass all country totals for the year; Map grays out countries outside region.
  $: filteredData = mapData.filter(d => d.year === selectedYear);

  // ── conflict panel ────────────────────────────────────────────────────────
  $: panelConflicts = selectedCountry
    ? allConflicts.filter(c => c.year === selectedYear && c.country === selectedCountry)
    : [];

  // ── time series ───────────────────────────────────────────────────────────
  // Filtered by selectedCountry AND selectedRegion; x = year.
  $: timeSeriesData = (() => {
    let rows = allConflicts;
    if (selectedCountry) rows = rows.filter(c => c.country === selectedCountry);
    if (selectedRegion)  rows = rows.filter(c => c.region  === selectedRegion);
    const byYear = new Map();
    rows.forEach(c => byYear.set(c.year, (byYear.get(c.year) || 0) + c.best));
    return [...byYear.entries()]
      .map(([year, deaths]) => ({ year, deaths }))
      .sort((a, b) => a.year - b.year);
  })();

  $: timeSeriesLabel = [
    selectedCountry && selectedCountry,
    selectedRegion  && selectedRegion,
  ].filter(Boolean).join(' · ');

  // ── region bar ────────────────────────────────────────────────────────────
  // Filtered by selectedYear only; shows all regions.
  $: regionData = (() => {
    const rows = allConflicts.filter(c => c.year === selectedYear);
    const byRegion = new Map();
    rows.forEach(c => byRegion.set(c.region, (byRegion.get(c.region) || 0) + c.best));
    return [...byRegion.entries()]
      .map(([region, deaths]) => ({ region, deaths }))
      .sort((a, b) => b.deaths - a.deaths);
  })();

  // ── country rank ──────────────────────────────────────────────────────────
  // Filtered by selectedYear + selectedRegion; shows top 10.
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

  // ── event handlers ────────────────────────────────────────────────────────
  function handleCountryClick(e) {
    const name = e.detail;

    if (selectedCountry === name) {
      selectedCountry = null;
      selectedRegion = null; // optional: reset region when deselecting
      return;
    }

    selectedCountry = name;

    // find region for this country
    const match = mapData.find(d => d.country === name && d.year === selectedYear);
    if (match) {
      selectedRegion = match.region;
    }
  }

  function handleCountrySelect(e) {
    const name = e.detail;

    selectedCountry = name;

    if (!name) {
      selectedRegion = null;
      return;
    }

    const match = mapData.find(d => d.country === name && d.year === selectedYear);
    if (match) {
      selectedRegion = match.region;
    }
  }

  function handleRegionSelect(e) {
    selectedCountry = null;
    selectedRegion = e.detail;  // null = deselect
  }

  function handleYearSelect(e) {
    selectedYear = e.detail;
  }
</script>

<h1>Conflict Events Dashboard</h1>

<div class="controls">
  <label>Year: <strong>{selectedYear}</strong></label>
  <input type="range" min="1989" max="2024" step="1" bind:value={selectedYear} />
  {#if selectedRegion || selectedCountry}
    <span class="active-filters">
      Filters:
      {#if selectedRegion}
        <button class="chip" on:click={() => selectedRegion = null}>{selectedRegion} ✕</button>
      {/if}
      {#if selectedCountry}
        <button class="chip" on:click={() => selectedCountry = null}>{selectedCountry} ✕</button>
      {/if}
    </span>
  {/if}
</div>

<!-- ── row 1: map + panel ──────────────────────────────────────────────── -->
<div class="layout-top">
  {#if geoData && mapData.length}
    <WorldMap
      {geoData}
      data={filteredData}
      {selectedCountry}
      {selectedRegion}
      on:countryClick={handleCountryClick}
    />
  {:else}
    <p class="loading">Loading…</p>
  {/if}

  {#if selectedCountry}

    {#if panelConflicts.length}
      <ConflictPanel
        country={selectedCountry}
        year={selectedYear}
        conflicts={panelConflicts}
        on:close={() => selectedCountry = null}
      />
    {:else}
      <div class="no-data">
        <strong>{selectedCountry}</strong> — no conflict data for {selectedYear}
        <button on:click={() => selectedCountry = null}>✕</button>
      </div>
    {/if}
  {/if}
</div>

<!-- ── row 2: 3 charts ────────────────────────────────────────────────── -->
{#if allConflicts.length}
  <div class="layout-charts">
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
    background: #fdecea;
    color: #c0392b;
    border: 1px solid #f5b7b1;
    border-radius: 12px;
    padding: 2px 10px;
    font-size: 0.78rem;
    cursor: pointer;
  }
  .chip:hover { background: #f5b7b1; }

  .layout-top {
    display: grid;
    grid-template-columns: 960px 540px;
    gap: 16px;
    align-items: flex-start;
    padding: 0 0 12px 16px;
  }

  .layout-charts {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 0 0 32px 16px;
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
  }

  .no-data button {
    margin-left: auto;
    background: none;
    border: none;
    cursor: pointer;
    color: #888;
    font-size: 1rem;
  }
</style>
