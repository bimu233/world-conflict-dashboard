<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  export let country;
  export let year;
  // conflicts: [{..., deaths_c1, deaths_c2, source_offices, source_originals, best}]
  export let conflicts;

  const dispatch = createEventDispatcher();

  // ── pie data ─────────────────────────────────────────────────────────────────
  $: totalC1 = conflicts.reduce((s, c) => s + (c.deaths_c1 ?? 0), 0);
  $: totalC2 = conflicts.reduce((s, c) => s + (c.deaths_c2 ?? 0), 0);
  $: totalDeaths = totalC1 + totalC2;

  const COLORS = { c1: '#2ecc71', c2: '#e67e22' };

  // Build pie slices reactively using D3 math (no DOM writes)
  const W = 200, H = 200, cx = 100, cy = 100, R = 82, r = 38;

  $: pieInput = [
    { key: 'c1', label: 'High Clarity (1)', value: totalC1,  color: COLORS.c1 },
    { key: 'c2', label: 'Aggregated (2)',   value: totalC2,  color: COLORS.c2 },
  ].filter(d => d.value > 0);

  $: arcs = (() => {
    const pie = d3.pie().value(d => d.value).sort(null).padAngle(0.02);
    const arcGen = d3.arc().innerRadius(r).outerRadius(R);
    return pie(pieInput).map(a => ({
      ...a.data,
      path: arcGen(a),
      pct: totalDeaths > 0 ? Math.round(a.data.value / totalDeaths * 100) : 0,
    }));
  })();

  // ── source info ───────────────────────────────────────────────────────────────
  $: topOffices = (() => {
    const counts = new Map();
    conflicts.forEach(c => {
      (c.source_offices ?? '').split(';').map(s => s.trim()).filter(Boolean)
        .forEach(o => counts.set(o, (counts.get(o) ?? 0) + 1));
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
  })();

  $: topOriginals = (() => {
    const counts = new Map();
    conflicts.forEach(c => {
      (c.source_originals ?? '').split(';').map(s => s.trim()).filter(Boolean)
        .forEach(o => counts.set(o, (counts.get(o) ?? 0) + 1));
    });
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
  })();

  function pct(v) {
    return totalDeaths > 0 ? Math.round(v / totalDeaths * 100) : 0;
  }
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2>{country}</h2>
      <span class="year-badge">{year}</span>
    </div>
    <button class="close-btn" on:click={() => dispatch('close')}>✕</button>
  </div>

  <p class="subtitle">Source Clarity &amp; Evidence Quality</p>

  <!-- ── pie chart ─────────────────────────────────────────────────────────── -->
  <div class="chart-row">
    {#if arcs.length}
      <svg width={W} height={H}>
        {#each arcs as a}
          <path d={a.path} fill={a.color} stroke="#fff" stroke-width="2"
            transform={`translate(${cx},${cy})`} />
        {/each}
        <!-- centre label -->
        <text x={cx} y={cy - 6} text-anchor="middle" class="centre-val">
          {totalDeaths.toLocaleString()}
        </text>
        <text x={cx} y={cy + 12} text-anchor="middle" class="centre-lbl">deaths</text>
      </svg>
    {:else}
      <div class="no-chart">No data</div>
    {/if}

    <div class="legend">
      {#each pieInput as d}
        <div class="legend-item">
          <span class="dot" style="background:{d.color}"></span>
          <div class="legend-text">
            <span class="legend-label">{d.label}</span>
            <span class="legend-sub">{d.value.toLocaleString()} deaths ({pct(d.value)}%)</span>
          </div>
        </div>
      {/each}

      <div class="clarity-def">
        <div class="def-row">
          <span class="dot" style="background:{COLORS.c1}"></span>
          <span><strong>Clarity 1:</strong> Individual incident fully identified from source — specific time, place, actors.</span>
        </div>
        <div class="def-row">
          <span class="dot" style="background:{COLORS.c2}"></span>
          <span><strong>Clarity 2:</strong> Aggregated report spanning multiple incidents or days — cannot be disaggregated.</span>
        </div>
      </div>
    </div>
  </div>

  <!-- ── source organizations ──────────────────────────────────────────────── -->
  {#if topOffices.length}
    <div class="section">
      <h3 class="section-title">Source Organizations</h3>
      <div class="tag-list">
        {#each topOffices as [name, count]}
          <span class="tag">{name} <span class="tag-count">{count}</span></span>
        {/each}
      </div>
    </div>
  {/if}

  <!-- ── source originals ──────────────────────────────────────────────────── -->
  {#if topOriginals.length}
    <div class="section">
      <h3 class="section-title">Original Informants</h3>
      <p class="section-desc">Who reported the information in the primary source.</p>
      <div class="tag-list">
        {#each topOriginals as [name, count]}
          <span class="tag secondary">{name} <span class="tag-count">{count}</span></span>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    width: 100%;
    box-sizing: border-box;
    max-height: 466px;
    overflow-y: auto;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 4px;
  }

  h2 { margin: 0; font-size: 1.2rem; }

  .year-badge {
    font-size: 0.85rem;
    background: #eee;
    border-radius: 4px;
    padding: 2px 8px;
    color: #555;
  }

  .subtitle {
    margin: 4px 0 10px;
    font-size: 0.85rem;
    color: #666;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: #888;
    padding: 2px 6px;
  }
  .close-btn:hover { color: #000; }

  /* ── chart row ── */
  .chart-row {
    display: flex;
    gap: 12px;
    align-items: center;
    margin-bottom: 12px;
  }

  .no-chart {
    width: 200px;
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #aaa;
    font-size: 0.85rem;
  }

  .centre-val {
    font-size: 18px;
    font-weight: 700;
    fill: #222;
  }
  .centre-lbl {
    font-size: 11px;
    fill: #888;
  }

  /* ── legend ── */
  .legend {
    display: flex;
    flex-direction: column;
    gap: 8px;
    flex: 1;
  }

  .legend-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
  }

  .dot {
    display: inline-block;
    width: 11px;
    height: 11px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 3px;
  }

  .legend-text {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .legend-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #222;
  }

  .legend-sub {
    font-size: 0.75rem;
    color: #666;
  }

  .clarity-def {
    margin-top: 6px;
    padding: 8px 10px;
    background: #f9f9f9;
    border-left: 3px solid #ddd;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    gap: 5px;
  }

  .def-row {
    display: flex;
    align-items: flex-start;
    gap: 6px;
    font-size: 0.74rem;
    color: #555;
    line-height: 1.4;
  }

  /* ── sections ── */
  .section {
    border-top: 1px solid #eee;
    padding-top: 10px;
    margin-top: 4px;
  }

  .section-title {
    margin: 0 0 4px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #333;
  }

  .section-desc {
    margin: 0 0 6px;
    font-size: 0.74rem;
    color: #888;
  }

  .tag-list {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }

  .tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: #eef4fb;
    color: #2c3e50;
    border-radius: 12px;
    padding: 2px 9px;
    font-size: 0.74rem;
  }

  .tag.secondary {
    background: #fef9ec;
    color: #7d5a00;
  }

  .tag-count {
    font-size: 0.68rem;
    color: #888;
    background: rgba(0,0,0,0.07);
    border-radius: 8px;
    padding: 0 4px;
  }
</style>
