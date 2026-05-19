<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // data: [{iso3, country, gdp_growth, fdi_pct_gdp}] — all countries for selected year
  export let data           = [];
  export let selectedCountry = '';
  export let year           = null;

  const dispatch = createEventDispatcher();

  const width  = 540;
  const height = 180;
  const margin = { top: 16, right: 24, bottom: 44, left: 60 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: vals = data.filter(d => d.gdp_growth != null && d.fdi_pct_gdp != null);

  $: xDom = (() => {
    if (!vals.length) return [-10, 10];
    const [lo, hi] = d3.extent(vals, d => d.gdp_growth);
    const pad = (hi - lo) * 0.08 || 2;
    return [lo - pad, hi + pad];
  })();

  $: yDom = (() => {
    if (!vals.length) return [0, 20];
    const [lo, hi] = d3.extent(vals, d => d.fdi_pct_gdp);
    const pad = (hi - lo) * 0.08 || 2;
    return [lo - pad, hi + pad];
  })();

  $: xScale = d3.scaleLinear().domain(xDom).nice().range([0, iW]);
  $: yScale = d3.scaleLinear().domain(yDom).nice().range([iH, 0]);

  $: xTicks = xScale.ticks(6);
  $: yTicks = yScale.ticks(4);

  $: zeroX = xScale.domain()[0] <= 0 && xScale.domain()[1] >= 0 ? xScale(0) : null;
  $: zeroY = yScale.domain()[0] <= 0 && yScale.domain()[1] >= 0 ? yScale(0) : null;

  $: sel = vals.find(d => d.country === selectedCountry) ?? null;

  function fmt(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">GDP Growth vs FDI Inflows</span>
    {#if year}<span class="year-badge">{year}</span>{/if}
    <span class="hint">click to select</span>
  </div>

  {#if !vals.length}
    <p class="empty">No data for selected year.</p>
  {:else}
    <svg viewBox="0 0 {width} {height}" style="width:100%;height:{height}px;display:block;">
      <g transform={`translate(${margin.left},${margin.top})`}>

        <!-- grid + x-axis labels -->
        {#each xTicks as tick}
          <line x1={xScale(tick)} x2={xScale(tick)} y1={0} y2={iH} class="grid-line" />
          <text x={xScale(tick)} y={iH + 14} class="axis-label" text-anchor="middle">{tick}%</text>
        {/each}

        <!-- y-axis labels + grid -->
        {#each yTicks as tick}
          <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
          <text x={-6} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">{tick}%</text>
        {/each}

        <!-- axis lines -->
        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />
        <line x1={0} x2={0}  y1={0}  y2={iH} class="axis-line" />

        <!-- zero reference lines -->
        {#if zeroX !== null}
          <line x1={zeroX} x2={zeroX} y1={0} y2={iH} class="zero-line" />
        {/if}
        {#if zeroY !== null}
          <line x1={0} x2={iW} y1={zeroY} y2={zeroY} class="zero-line" />
        {/if}

        <!-- axis titles -->
        <text
          x={iW / 2} y={iH + 36}
          class="axis-title" text-anchor="middle"
        >GDP Growth %</text>
        <text
          transform={`translate(${-46},${iH / 2}) rotate(-90)`}
          class="axis-title" text-anchor="middle"
        >FDI % of GDP</text>

        <!-- all country dots (non-selected) -->
        {#each vals as d}
          {#if d.country !== selectedCountry}
            <circle
              cx={xScale(d.gdp_growth)}
              cy={yScale(d.fdi_pct_gdp)}
              r="2.5"
              class="dot"
              style="cursor:pointer"
              on:click={() => dispatch('countrySelect', d.country)}
            >
              <title>{d.country}: GDP {fmt(d.gdp_growth)}, FDI {fmt(d.fdi_pct_gdp)}</title>
            </circle>
          {/if}
        {/each}

        <!-- selected country: drawn on top -->
        {#if sel}
          {@const cx = xScale(sel.gdp_growth)}
          {@const cy = yScale(sel.fdi_pct_gdp)}
          {@const labelRight = cx < iW * 0.75}
          <circle {cx} {cy} r="5" class="dot-selected" />
          <text
            x={labelRight ? cx + 7 : cx - 7}
            y={cy}
            class="dot-label"
            text-anchor={labelRight ? 'start' : 'end'}
            dy="0.35em"
          >{sel.country}</text>
        {/if}

      </g>
    </svg>
  {/if}
</div>

<style>
  .chart-box {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px 12px 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    width: 100%;
    height: 100%;
    box-sizing: border-box;
  }

  .chart-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 2px;
  }

  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }

  .year-badge {
    font-size: 0.75rem;
    background: #f0f3f4;
    color: #555;
    border-radius: 4px;
    padding: 1px 6px;
  }

  .hint { font-size: 0.72rem; color: #aaa; margin-left: auto; }

  .empty { font-size: 0.82rem; color: #999; text-align: center; padding: 20px 0; margin: 0; }

  .grid-line { stroke: #eee; stroke-width: 1; }
  .axis-line { stroke: #ccc; stroke-width: 1; }
  .zero-line { stroke: #bbb; stroke-width: 1; stroke-dasharray: 3,3; }

  .axis-label {
    font-size: 9px;
    fill: #666;
    font-family: system-ui, sans-serif;
  }

  .axis-title {
    font-size: 10px;
    fill: #888;
    font-family: system-ui, sans-serif;
  }

  .dot {
    fill: rgba(41, 128, 185, 0.45);
    stroke: rgba(41, 128, 185, 0.7);
    stroke-width: 0.5;
  }

  .dot:hover { fill: rgba(41, 128, 185, 0.75); }

  .dot-selected {
    fill: #e67e22;
    stroke: white;
    stroke-width: 1.5;
  }

  .dot-label {
    font-size: 10px;
    fill: #e67e22;
    font-weight: 600;
    font-family: system-ui, sans-serif;
    pointer-events: none;
  }
</style>
