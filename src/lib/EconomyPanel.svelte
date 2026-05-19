<script>
  import { createEventDispatcher } from 'svelte';

  // row: {year, gdp_growth, fdi_pct_gdp, trade_pct_gdp} for selected country+year
  // prevRow: same for year-1 (to show direction arrows)
  export let country  = '';
  export let year     = null;
  export let row      = null;
  export let prevRow  = null;

  const dispatch = createEventDispatcher();

  const STATS = [
    { key: 'gdp_growth',    label: 'GDP Growth',    unit: '%', color: '#27ae60' },
    { key: 'fdi_pct_gdp',   label: 'FDI Inflows',  unit: '% of GDP', color: '#8e44ad' },
    { key: 'trade_pct_gdp', label: 'Trade Openness', unit: '% of GDP', color: '#2980b9' },
  ];

  function fmt(v) {
    if (v == null) return '—';
    return (v >= 0 ? '+' : '') + v.toFixed(1);
  }

  function arrow(key) {
    if (!row || !prevRow || row[key] == null || prevRow[key] == null) return '';
    return row[key] > prevRow[key] ? '▲' : row[key] < prevRow[key] ? '▼' : '●';
  }

  function arrowClass(key) {
    if (!row || !prevRow || row[key] == null || prevRow[key] == null) return '';
    return row[key] > prevRow[key] ? 'up' : row[key] < prevRow[key] ? 'down' : '';
  }
</script>

<div class="panel">
  <div class="panel-header">
    <span class="panel-title">Economy</span>
    {#if country}<span class="country-badge">{country}</span>{/if}
    {#if year}<span class="year-badge">{year}</span>{/if}
    <button class="close-btn" on:click={() => dispatch('close')}>✕</button>
  </div>

  {#if !country}
    <p class="empty">Click a country on the map.</p>
  {:else if !row}
    <p class="empty">No WDI data for {country} in {year}.</p>
  {:else}
    <div class="stat-grid">
      {#each STATS as s}
        <div class="stat-card">
          <div class="stat-top">
            <span class="stat-val" style="color:{s.color}">
              {fmt(row[s.key])}<span class="stat-unit">{s.unit}</span>
            </span>
            <span class="arrow {arrowClass(s.key)}">{arrow(s.key)}</span>
          </div>
          <div class="stat-label">{s.label}</div>
        </div>
      {/each}
    </div>
    <p class="note">▲▼ vs {year - 1}</p>
  {/if}
</div>

<style>
  .panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    box-sizing: border-box;
    width: 100%;
  }
  .panel-header {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 6px;
    flex-wrap: wrap;
  }
  .panel-title { font-size: 0.82rem; font-weight: 600; color: #222; }
  .country-badge {
    font-size: 0.75rem;
    background: #eafaf1;
    color: #27ae60;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .year-badge {
    font-size: 0.75rem;
    background: #f0f3f4;
    color: #555;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .close-btn {
    margin-left: auto;
    background: none;
    border: none;
    cursor: pointer;
    color: #aaa;
    font-size: 0.9rem;
  }
  .close-btn:hover { color: #555; }
  .empty { font-size: 0.82rem; color: #999; text-align: center; padding: 12px 0; margin: 0; }
  .stat-grid { display: flex; flex-direction: row; gap: 8px; }
  .stat-card {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 6px 8px;
    display: flex;
    flex-direction: column;
    gap: 1px;
    flex: 1;
  }
  .stat-top { display: flex; align-items: baseline; justify-content: space-between; }
  .stat-val { font-size: 1.05rem; font-weight: 700; line-height: 1.1; }
  .stat-unit { font-size: 0.60rem; font-weight: 400; color: #888; margin-left: 2px; }
  .stat-label { font-size: 0.65rem; color: #666; }
  .arrow { font-size: 0.75rem; }
  .arrow.up   { color: #27ae60; }
  .arrow.down { color: #c0392b; }
  .note { font-size: 0.65rem; color: #bbb; margin: 4px 0 0; text-align: right; }
</style>
