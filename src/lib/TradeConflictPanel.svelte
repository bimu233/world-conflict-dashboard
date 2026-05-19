<script>
  import { createEventDispatcher } from 'svelte';

  export let country    = '';
  export let series     = [];     // [{year, deaths, tradePct}]
  export let gdpSeries  = [];     // [{year, deaths, gdpGrowth}]

  const dispatch = createEventDispatcher();

  function pearson(pairs) {
    const valid = pairs.filter(d => d.x != null && d.y != null);
    if (valid.length < 3) return null;
    const n  = valid.length;
    const xm = valid.reduce((s, d) => s + d.x, 0) / n;
    const ym = valid.reduce((s, d) => s + d.y, 0) / n;
    let num = 0, dx2 = 0, dy2 = 0;
    valid.forEach(d => {
      const dx = d.x - xm, dy = d.y - ym;
      num += dx * dy; dx2 += dx * dx; dy2 += dy * dy;
    });
    return { v: dx2 > 0 && dy2 > 0 ? num / Math.sqrt(dx2 * dy2) : 0, n };
  }

  $: tradeR = pearson(series.map(d  => ({ x: d.deaths, y: d.tradePct  })));
  $: gdpR   = pearson(gdpSeries.map(d => ({ x: d.deaths, y: d.gdpGrowth })));

  function interp(v) {
    const a = Math.abs(v);
    if (a < 0.1) return 'negligible';
    if (a < 0.3) return 'weak';
    if (a < 0.5) return 'moderate';
    if (a < 0.7) return 'strong';
    return 'very strong';
  }
  function sign(v) { return v >= 0 ? 'positive' : 'negative'; }
  function fmtR(v) { return (v >= 0 ? '+' : '') + v.toFixed(3); }
</script>

<div class="panel">
  <div class="panel-header">
    <span class="panel-title">Conflict Relationships</span>
    {#if country}<span class="country-badge">{country}</span>{/if}
    <button class="close-btn" on:click={() => dispatch('close')}>✕</button>
  </div>

  {#if !country}
    <p class="empty">Click a country on the map to see statistics.</p>
  {:else if !tradeR && !gdpR}
    <p class="empty">Not enough overlapping data for {country}.</p>
  {:else}
    <div class="r-grid">

      {#if tradeR}
        <div class="r-card">
          <div class="r-val {tradeR.v >= 0 ? 'pos' : 'neg'}">{fmtR(tradeR.v)}</div>
          <div class="r-label">Deaths vs Trade % Chg <span class="r-n">({tradeR.n} yrs)</span></div>
          <div class="r-desc">{interp(tradeR.v)} {sign(tradeR.v)} correlation</div>
        </div>
      {/if}

      {#if gdpR}
        <div class="r-card">
          <div class="r-val {gdpR.v >= 0 ? 'pos' : 'neg'}">{fmtR(gdpR.v)}</div>
          <div class="r-label">Deaths vs GDP Growth <span class="r-n">({gdpR.n} yrs)</span></div>
          <div class="r-desc">{interp(gdpR.v)} {sign(gdpR.v)} correlation</div>
        </div>
      {/if}

    </div>
  {/if}
</div>

<style>
  .panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 8px 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    align-self: stretch;
    min-width: 200px;
    max-width: 280px;
    box-sizing: border-box;
  }
  .panel-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
  .panel-title { font-size: 0.88rem; font-weight: 600; color: #222; }
  .country-badge {
    font-size: 0.75rem;
    background: #eaf4fb;
    color: #2980b9;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .close-btn { margin-left: auto; background: none; border: none; cursor: pointer; color: #aaa; font-size: 0.9rem; }
  .close-btn:hover { color: #555; }
  .empty { font-size: 0.82rem; color: #999; text-align: center; padding: 8px 0; margin: 0; }
  .r-grid { display: flex; flex-direction: row; gap: 8px; }
  .r-card { background: #f8f9fa; border-radius: 6px; padding: 6px 10px; flex: 1; }
  .r-val { font-size: 1.3rem; font-weight: 700; line-height: 1.1; }
  .r-val.pos { color: #27ae60; }
  .r-val.neg { color: #c0392b; }
  .r-label { font-size: 0.68rem; font-weight: 600; color: #555; margin-top: 2px; }
  .r-n { font-weight: 400; color: #999; }
  .r-desc { font-size: 0.66rem; color: #888; margin-top: 2px; }
</style>
