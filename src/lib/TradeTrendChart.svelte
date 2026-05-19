<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // [{year, exports_usd, imports_usd}] sorted by year
  export let trendData = [];
  export let selectedYear;
  export let filterLabel = '';

  const dispatch = createEventDispatcher();

  const width  = 520;
  const height = 210;
  const margin = { top: 24, right: 20, bottom: 32, left: 72 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  function fmtUSD(v) {
    if (!v && v !== 0) return '0';
    if (v >= 1e12) return '$' + (v / 1e12).toFixed(1) + 'T';
    if (v >= 1e9)  return '$' + (v / 1e9).toFixed(1)  + 'B';
    if (v >= 1e6)  return '$' + (v / 1e6).toFixed(1)  + 'M';
    if (v >= 1e3)  return '$' + (v / 1e3).toFixed(1)  + 'K';
    return '$' + v.toLocaleString();
  }

  $: xScale = d3.scaleLinear()
    .domain(
      trendData.length
        ? [d3.min(trendData, d => d.year), d3.max(trendData, d => d.year)]
        : [1995, 2023]
    )
    .range([0, iW]);

  $: yMax = trendData.length
    ? d3.max(trendData, d => Math.max(Number(d.exports_usd) || 0, Number(d.imports_usd) || 0))
    : 1;

  $: yScale = d3.scaleLinear()
    .domain([0, yMax || 1])
    .nice()
    .range([iH, 0]);

  $: exportLine = trendData.length >= 2
    ? d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(Number(d.exports_usd) || 0))
        (trendData)
    : null;

  $: importLine = trendData.length >= 2
    ? d3.line()
        .x(d => xScale(d.year))
        .y(d => yScale(Number(d.imports_usd) || 0))
        (trendData)
    : null;

  $: xTicks = xScale.ticks(7);
  $: yTicks = yScale.ticks(4);

  // Legend position: top-right of chart area
  const legendX = iW - 110;
  const legendY = 2;
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Trade Over Time</span>
    {#if filterLabel}<span class="filter-badge">{filterLabel}</span>{/if}
    <span class="hint">click a dot to set year</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      <!-- Y grid lines + labels -->
      {#each yTicks as tick}
        <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
        <text x={-8} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">
          {fmtUSD(tick)}
        </text>
      {/each}

      <!-- X axis labels -->
      {#each xTicks as tick}
        <text x={xScale(tick)} y={iH + 20} class="axis-label" text-anchor="middle">{tick}</text>
      {/each}
      <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />

      {#if trendData.length === 0}
        <!-- Empty state -->
        <text
          x={iW / 2} y={iH / 2}
          text-anchor="middle" dominant-baseline="middle"
          class="empty-text"
        >Select a country to view trade trend</text>
      {:else}
        <!-- Export line -->
        {#if exportLine}
          <path d={exportLine} fill="none" stroke="#2980b9" stroke-width="2" />
        {/if}

        <!-- Import line -->
        {#if importLine}
          <path d={importLine} fill="none" stroke="#e67e22" stroke-width="2" />
        {/if}

        <!-- Selected year vertical indicator -->
        <line
          x1={xScale(selectedYear)} x2={xScale(selectedYear)}
          y1={0} y2={iH}
          stroke="#e67e22" stroke-width="1.5" stroke-dasharray="4,3"
        />

        <!-- Export dots -->
        {#each trendData as d}
          <circle
            cx={xScale(d.year)}
            cy={yScale(Number(d.exports_usd) || 0)}
            r={d.year === selectedYear ? 5 : 3}
            fill={d.year === selectedYear ? '#1a5f8a' : '#2980b9'}
            stroke="white" stroke-width="1"
            style="cursor:pointer"
            on:click={() => dispatch('yearSelect', d.year)}
          >
            <title>{d.year} Exports: {fmtUSD(Number(d.exports_usd))}</title>
          </circle>
        {/each}

        <!-- Import dots -->
        {#each trendData as d}
          <circle
            cx={xScale(d.year)}
            cy={yScale(Number(d.imports_usd) || 0)}
            r={d.year === selectedYear ? 5 : 3}
            fill={d.year === selectedYear ? '#b05a10' : '#e67e22'}
            stroke="white" stroke-width="1"
            style="cursor:pointer"
            on:click={() => dispatch('yearSelect', d.year)}
          >
            <title>{d.year} Imports: {fmtUSD(Number(d.imports_usd))}</title>
          </circle>
        {/each}
      {/if}

      <!-- Legend (top-right, inside chart area) -->
      <g transform={`translate(${legendX},${legendY})`}>
        <rect x={0} y={0} width={10} height={10} fill="#2980b9" rx="2" />
        <text x={14} y={9} class="legend-label">Exports</text>
        <rect x={0} y={16} width={10} height={10} fill="#e67e22" rx="2" />
        <text x={14} y={25} class="legend-label">Imports</text>
      </g>

    </g>
  </svg>
</div>

<style>
  .chart-box {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px 12px 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    font-family: system-ui, sans-serif;
  }

  .chart-header {
    display: flex;
    align-items: baseline;
    gap: 8px;
    margin-bottom: 2px;
  }

  .chart-title {
    font-size: 0.9rem;
    font-weight: 600;
    color: #222;
  }

  .filter-badge {
    font-size: 0.75rem;
    background: #e8f4fd;
    color: #2980b9;
    border-radius: 4px;
    padding: 1px 6px;
  }

  .hint {
    font-size: 0.72rem;
    color: #aaa;
    margin-left: auto;
  }

  .grid-line {
    stroke: #eee;
    stroke-width: 1;
  }

  .axis-line {
    stroke: #ccc;
  }

  .axis-label {
    font-size: 10px;
    fill: #666;
    font-family: system-ui, sans-serif;
  }

  .legend-label {
    font-size: 10px;
    fill: #444;
    font-family: system-ui, sans-serif;
    dominant-baseline: auto;
  }

  .empty-text {
    font-size: 13px;
    fill: #aaa;
    font-family: system-ui, sans-serif;
    font-style: italic;
  }
</style>
