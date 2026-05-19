<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // series: [{year, gdp_growth, fdi_pct_gdp, trade_pct_gdp}]
  export let series        = [];
  export let selectedYear;
  export let filterLabel   = '';

  const dispatch = createEventDispatcher();

  const width  = 540;
  const height = 180;
  const margin = { top: 24, right: 16, bottom: 32, left: 52 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  const METRICS = [
    { key: 'gdp_growth',    label: 'GDP Growth %',    color: '#27ae60', dash: ''    },
    { key: 'fdi_pct_gdp',   label: 'FDI % of GDP',    color: '#8e44ad', dash: '4,3' },
    { key: 'trade_pct_gdp', label: 'Trade % of GDP',  color: '#2980b9', dash: '2,2' },
  ];

  $: validSeries = series.filter(d => d.year != null);

  $: xScale = d3.scaleLinear()
    .domain(validSeries.length ? [d3.min(validSeries, d => d.year), d3.max(validSeries, d => d.year)] : [1989, 2024])
    .range([0, iW]);

  $: yExtent = (() => {
    const vals = validSeries.flatMap(d =>
      METRICS.map(m => d[m.key]).filter(v => v != null)
    );
    if (!vals.length) return [-10, 10];
    const lo = d3.min(vals), hi = d3.max(vals);
    const pad = (hi - lo) * 0.08 || 5;
    return [lo - pad, hi + pad];
  })();

  $: yScale = d3.scaleLinear().domain(yExtent).nice().range([iH, 0]);

  $: lines = METRICS.map(m => ({
    ...m,
    path: validSeries.filter(d => d[m.key] != null).length >= 2
      ? d3.line()
          .defined(d => d[m.key] != null)
          .x(d => xScale(d.year))
          .y(d => yScale(d[m.key]))
          (validSeries)
      : null,
  }));

  $: xTicks = xScale.ticks(7);
  $: yTicks = yScale.ticks(5);
  $: zeroY  = yScale(0);

  function fmt(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Economic Indicators Over Time</span>
    {#if filterLabel}<span class="filter-badge">{filterLabel}</span>{/if}
    <span class="hint">click to set year</span>
  </div>
  <div class="legend">
    {#each METRICS as m}
      <span class="leg-item">
        <svg width="22" height="10">
          <line x1="0" y1="5" x2="22" y2="5"
            stroke={m.color} stroke-width="2"
            stroke-dasharray={m.dash || 'none'} />
        </svg>
        <span class="leg-lbl">{m.label}</span>
      </span>
    {/each}
  </div>

  {#if !validSeries.length}
    <p class="empty">No data for selected country.</p>
  {:else}
    <svg viewBox="0 0 {width} {height}" style="width:100%;height:{height}px;display:block;">
      <g transform={`translate(${margin.left},${margin.top})`}>

        {#each yTicks as tick}
          <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
          <text x={-6} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">
            {fmt(tick)}
          </text>
        {/each}

        {#each xTicks as tick}
          <text x={xScale(tick)} y={iH + 20} class="axis-label" text-anchor="middle">{tick}</text>
        {/each}
        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />

        {#if zeroY >= 0 && zeroY <= iH}
          <line x1={0} x2={iW} y1={zeroY} y2={zeroY} class="zero-line" />
        {/if}

        {#each lines as m}
          {#if m.path}
            <path d={m.path} fill="none" stroke={m.color} stroke-width="1.8"
              stroke-dasharray={m.dash || 'none'} />
          {/if}
        {/each}

        <!-- dots for selected year -->
        {#each METRICS as m}
          {#each validSeries.filter(d => d[m.key] != null) as d}
            <circle
              cx={xScale(d.year)} cy={yScale(d[m.key])}
              r={d.year === selectedYear ? 4.5 : 0}
              fill={m.color} stroke="white" stroke-width="1"
            />
          {/each}
        {/each}

        <!-- year indicator -->
        <line
          x1={xScale(selectedYear)} x2={xScale(selectedYear)}
          y1={0} y2={iH}
          stroke="#e67e22" stroke-width="1.5" stroke-dasharray="4,3"
        />

        <!-- invisible hit targets -->
        {#each validSeries as d}
          <rect
            x={xScale(d.year) - 6} y={0}
            width={12} height={iH}
            fill="transparent"
            style="cursor:pointer"
            on:click={() => dispatch('yearSelect', d.year)}
          />
        {/each}

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
    box-sizing: border-box;
  }
  .chart-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 2px;
  }
  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }
  .filter-badge {
    font-size: 0.75rem;
    background: #eafaf1;
    color: #27ae60;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .hint { font-size: 0.72rem; color: #aaa; margin-left: auto; }
  .legend {
    display: flex;
    gap: 10px;
    align-items: center;
    margin-bottom: 2px;
    flex-wrap: wrap;
  }
  .leg-item { display: flex; align-items: center; gap: 4px; }
  .leg-lbl { font-size: 0.70rem; color: #666; }
  .empty { font-size: 0.82rem; color: #999; padding: 20px 0; text-align: center; margin: 0; }
  .grid-line { stroke: #eee; stroke-width: 1; }
  .zero-line { stroke: #ccc; stroke-width: 1; stroke-dasharray: 3,2; }
  .axis-line { stroke: #ccc; }
  .axis-label { font-size: 10px; fill: #666; font-family: system-ui, sans-serif; }
</style>
