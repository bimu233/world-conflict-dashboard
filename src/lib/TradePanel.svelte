<script>
  import { createEventDispatcher } from 'svelte';

  export let country;
  export let year;
  export let tradePartners = []; // [{partner_name, partner_iso3, total_usd, exports_usd, imports_usd}]
  export let worldTotal = null;  // {year, exports_usd, imports_usd} | null

  const dispatch = createEventDispatcher();

  function fmtUSD(v) {
    if (v == null || v === '') return '—';
    const n = Number(v);
    if (isNaN(n)) return '—';
    if (n >= 1e12) return '$' + (n / 1e12).toFixed(1) + 'T';
    if (n >= 1e9)  return '$' + (n / 1e9).toFixed(1)  + 'B';
    if (n >= 1e6)  return '$' + (n / 1e6).toFixed(1)  + 'M';
    if (n >= 1e3)  return '$' + (n / 1e3).toFixed(1)  + 'K';
    return '$' + n.toLocaleString();
  }

  $: balance = worldTotal ? (Number(worldTotal.exports_usd) - Number(worldTotal.imports_usd)) : 0;
  $: balancePositive = balance >= 0;
</script>

<div class="panel">
  <div class="panel-header">
    <div class="header-left">
      <h2>{country}</h2>
      <span class="year-badge">{year}</span>
    </div>
    <button class="close-btn" on:click={() => dispatch('close')}>✕</button>
  </div>

  {#if worldTotal}
    <div class="stats-row">
      <div class="stat-box">
        <div class="stat-label">Exports</div>
        <div class="stat-value exports">{fmtUSD(worldTotal.exports_usd)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Imports</div>
        <div class="stat-value imports">{fmtUSD(worldTotal.imports_usd)}</div>
      </div>
      <div class="stat-box">
        <div class="stat-label">Balance</div>
        <div class="stat-value" class:positive={balancePositive} class:negative={!balancePositive}>
          {balancePositive ? '+' : ''}{fmtUSD(balance)}
        </div>
      </div>
    </div>
  {/if}

  {#if tradePartners.length > 0}
    <div class="trade-section">
      <h3 class="trade-title">Top Trading Partners <span class="trade-year">{year}</span></h3>
      <div class="table-wrap">
        <table class="trade-table">
          <thead>
            <tr>
              <th class="rank">#</th>
              <th>Partner</th>
              <th class="num">Exports</th>
              <th class="num">Imports</th>
              <th class="num">Total</th>
            </tr>
          </thead>
          <tbody>
            {#each tradePartners.slice(0, 10) as p, i}
              <tr>
                <td class="rank muted">{i + 1}</td>
                <td>{p.partner_name}</td>
                <td class="num">{fmtUSD(p.exports_usd)}</td>
                <td class="num">{fmtUSD(p.imports_usd)}</td>
                <td class="num total-usd">{fmtUSD(p.total_usd)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {:else}
    <p class="no-trade">No bilateral trade data available for {year}.</p>
  {/if}

  <p class="source-note">Source: UN Comtrade Public API · Bilateral trade by commodity total</p>
</div>

<style>
  .panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    width: 100%;
    max-height: 466px;
    overflow-y: auto;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
    font-family: system-ui, sans-serif;
    box-sizing: border-box;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  h2 {
    margin: 0;
    font-size: 1.2rem;
    color: #1a1a1a;
  }

  .year-badge {
    font-size: 0.85rem;
    background: #eee;
    border-radius: 4px;
    padding: 2px 8px;
    color: #555;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: #888;
    padding: 2px 6px;
    line-height: 1;
  }
  .close-btn:hover { color: #000; }

  /* Stats row */
  .stats-row {
    display: flex;
    gap: 8px;
    margin-bottom: 14px;
  }

  .stat-box {
    flex: 1;
    background: #f9f9f9;
    border: 1px solid #eee;
    border-radius: 6px;
    padding: 8px 10px;
    text-align: center;
  }

  .stat-label {
    font-size: 0.72rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 3px;
  }

  .stat-value {
    font-size: 0.95rem;
    font-weight: 700;
    color: #333;
  }

  .stat-value.exports { color: #2980b9; }
  .stat-value.imports { color: #e67e22; }
  .stat-value.positive { color: #2980b9; }
  .stat-value.negative { color: #c0392b; }

  /* Trade partners table */
  .trade-section {
    border-top: 1px solid #eee;
    padding-top: 10px;
  }

  .trade-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #222;
    margin: 0 0 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .trade-year {
    font-size: 0.78rem;
    font-weight: 400;
    background: #e8f4fd;
    color: #2980b9;
    border-radius: 4px;
    padding: 1px 6px;
  }

  .table-wrap {
    overflow-x: auto;
  }

  .trade-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }

  .trade-table th {
    text-align: left;
    padding: 5px 7px;
    background: #f0f7ff;
    border-bottom: 2px solid #d0e8f8;
    white-space: nowrap;
    color: #2c3e50;
    font-weight: 600;
  }

  .trade-table td {
    padding: 4px 7px;
    border-bottom: 1px solid #f0f0f0;
    vertical-align: middle;
  }

  .trade-table tr:last-child td { border-bottom: none; }
  .trade-table tr:hover td { background: #f7fbff; }

  .num { text-align: right; }
  .rank { width: 24px; }
  .muted { color: #aaa; font-size: 0.78rem; }

  .total-usd {
    font-weight: 700;
    color: #2980b9;
  }

  .no-trade {
    margin: 12px 0 8px;
    font-size: 0.8rem;
    color: #aaa;
    font-style: italic;
  }

  .source-note {
    margin: 12px 0 0;
    font-size: 0.72rem;
    color: #bbb;
    border-top: 1px solid #f0f0f0;
    padding-top: 8px;
  }
</style>
