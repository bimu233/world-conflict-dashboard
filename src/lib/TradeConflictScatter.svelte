<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // scatterData: [{country, iso3, region, avgDeaths, avgTradePct}]
  export let scatterData = [];
  export let selectedCountry = '';

  const dispatch = createEventDispatcher();

  const width  = 400;
  const height = 280;
  const margin = { top: 24, right: 16, bottom: 48, left: 56 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: valid = scatterData.filter(d => d.avgDeaths > 0 && d.avgTradePct != null);

  // sqrt scale to reduce outlier dominance on x (deaths)
  $: xScale = d3.scaleSqrt()
    .domain([0, d3.max(valid, d => d.avgDeaths) || 1])
    .nice()
    .range([0, iW]);

  $: yExtent = (() => {
    const vals = valid.map(d => d.avgTradePct);
    const lo = Math.min(d3.min(vals) ?? 0, 0);
    const hi = Math.max(d3.max(vals) ?? 0, 0);
    return [lo * 1.15, hi * 1.15];
  })();
  $: yScale = d3.scaleLinear().domain(yExtent).nice().range([iH, 0]);

  $: regions = [...new Set(valid.map(d => d.region))].sort();
  $: colorScale = d3.scaleOrdinal(d3.schemeTableau10).domain(regions);

  $: xTicks = xScale.ticks(5);
  $: yTicks = yScale.ticks(5);
  $: zeroY  = yScale(0);

  function fmtD(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M';
    if (v >= 1_000)     return Math.round(v / 1_000) + 'k';
    return String(Math.round(v));
  }
  function fmtP(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Avg Deaths vs Avg Trade Change</span>
    <span class="sub">(per country, all years with data)</span>
  </div>

  {#if valid.length === 0}
    <p class="empty">No cross-country data available.</p>
  {:else}
    <svg {width} {height}>
      <g transform={`translate(${margin.left},${margin.top})`}>

        {#each yTicks as tick}
          <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
          <text x={-6} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">{fmtP(tick)}</text>
        {/each}

        {#each xTicks as tick}
          <line x1={xScale(tick)} x2={xScale(tick)} y1={0} y2={iH} class="grid-line" />
          <text x={xScale(tick)} y={iH + 14} class="axis-label" text-anchor="middle">{fmtD(tick)}</text>
        {/each}

        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />
        <line x1={0} x2={0}  y1={0}  y2={iH} class="axis-line" />

        {#if zeroY >= 0 && zeroY <= iH}
          <line x1={0} x2={iW} y1={zeroY} y2={zeroY} class="zero-line" />
        {/if}

        <!-- axis labels -->
        <text x={iW / 2} y={iH + 36} class="axis-title" text-anchor="middle">Avg Annual Deaths (√ scale)</text>
        <text
          x={-(iH / 2)} y={-44}
          class="axis-title"
          text-anchor="middle"
          transform="rotate(-90)"
        >Avg Trade % Change</text>

        <!-- dots -->
        {#each valid as d}
          {@const isSel = d.country === selectedCountry}
          <circle
            cx={xScale(d.avgDeaths)}
            cy={yScale(d.avgTradePct)}
            r={isSel ? 7 : 4}
            fill={colorScale(d.region)}
            stroke={isSel ? '#333' : 'rgba(255,255,255,0.7)'}
            stroke-width={isSel ? 2 : 0.8}
            opacity={isSel ? 1 : 0.7}
            style="cursor:pointer"
            on:click={() => dispatch('countrySelect', d.country)}
          >
            <title>{d.country} ({d.region})
Avg deaths: {Math.round(d.avgDeaths).toLocaleString()}
Avg trade chg: {fmtP(d.avgTradePct)}</title>
          </circle>
        {/each}

        <!-- label for selected country -->
        {#if selectedCountry}
          {@const sel = valid.find(d => d.country === selectedCountry)}
          {#if sel}
            <text
              x={xScale(sel.avgDeaths) + 9}
              y={yScale(sel.avgTradePct)}
              class="dot-label selected-label"
              dy="0.35em"
            >{sel.country}</text>
          {/if}
        {/if}

      </g>
    </svg>

    <!-- region color legend -->
    <div class="legend">
      {#each regions as r}
        <span class="leg-item">
          <span class="leg-dot" style="background:{colorScale(r)}"></span>
          <span class="leg-name">{r}</span>
        </span>
      {/each}
    </div>
  {/if}
</div>

<style>
  .chart-box {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px 12px 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }
  .chart-header { margin-bottom: 2px; }
  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }
  .sub { font-size: 0.72rem; color: #aaa; margin-left: 6px; }
  .grid-line { stroke: #eee; stroke-width: 1; }
  .zero-line { stroke: #bbb; stroke-width: 1; stroke-dasharray: 3,2; }
  .axis-line { stroke: #ccc; }
  .axis-label { font-size: 10px; fill: #666; font-family: system-ui, sans-serif; }
  .axis-title { font-size: 9px; fill: #888; font-family: system-ui, sans-serif; }
  .dot-label { font-size: 10px; fill: #333; font-family: system-ui, sans-serif; }
  .selected-label { font-weight: 600; fill: #222; }
  .empty { font-size: 0.82rem; color: #999; padding: 20px 0; text-align: center; }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 6px 12px;
    padding: 4px 4px 2px;
  }
  .leg-item { display: flex; align-items: center; gap: 4px; }
  .leg-dot {
    display: inline-block;
    width: 9px; height: 9px;
    border-radius: 50%;
    flex-shrink: 0;
  }
  .leg-name { font-size: 0.68rem; color: #555; }
</style>
