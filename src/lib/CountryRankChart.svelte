<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // rankData: [{country, deaths}] top-N, already filtered by year+region upstream
  export let rankData = [];
  export let selectedCountry = null;

  const dispatch = createEventDispatcher();

  const width  = 440;
  const height = 210;
  const margin = { top: 24, right: 60, bottom: 15, left: 110 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: yScale = d3.scaleBand()
    .domain(rankData.map(d => d.country))
    .range([0, iH])
    .padding(0.2);

  $: xScale = d3.scaleLinear()
    .domain([0, d3.max(rankData, d => d.deaths) || 1])
    .nice()
    .range([0, iW]);

  $: xTicks = xScale.ticks(3);

  function fmt(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1_000)     return Math.round(v / 1_000) + 'k';
    return String(v);
  }

  // Truncate long country names for the label
  function truncate(name, max = 14) {
    return name.length > max ? name.slice(0, max - 1) + '…' : name;
  }

  function toggle(country) {
    dispatch('countrySelect', selectedCountry === country ? null : country);
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Top Countries</span>
    <span class="hint">click to select country</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      <!-- grid lines + x labels -->
      {#each xTicks as tick}
        <line x1={xScale(tick)} x2={xScale(tick)} y1={0} y2={iH} class="grid-line" />
        <text x={xScale(tick)} y={iH + 14} class="axis-label" text-anchor="middle">{fmt(tick)}</text>
      {/each}

      <!-- bars -->
      {#each rankData as d}
        {@const active = selectedCountry === null || selectedCountry === d.country}
        <rect
          x={0}
          y={yScale(d.country)}
          width={xScale(d.deaths)}
          height={yScale.bandwidth()}
          fill={selectedCountry === d.country ? '#c0392b' : active ? '#e88080' : '#ddd'}
          rx="2"
          style="cursor:pointer"
          on:click={() => toggle(d.country)}
        >
          <title>{d.country}: {d.deaths.toLocaleString()} deaths</title>
        </rect>

        <!-- country label -->
        <text
          x={-6}
          y={yScale(d.country) + yScale.bandwidth() / 2}
          class="bar-label"
          class:active={active}
          text-anchor="end"
          dy="0.35em"
          style="cursor:pointer"
          on:click={() => toggle(d.country)}
        >
          {truncate(d.country)}
        </text>

        <!-- value label after bar -->
        <text
          x={xScale(d.deaths) + 4}
          y={yScale(d.country) + yScale.bandwidth() / 2}
          class="val-label"
          dy="0.35em"
        >
          {fmt(d.deaths)}
        </text>
      {/each}

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

  .hint {
    font-size: 0.72rem;
    color: #aaa;
    margin-left: auto;
  }

  .grid-line {
    stroke: #eee;
    stroke-width: 1;
  }

  .axis-label {
    font-size: 10px;
    fill: #666;
    font-family: system-ui, sans-serif;
  }

  .bar-label {
    font-size: 11px;
    fill: #999;
    font-family: system-ui, sans-serif;
  }

  .bar-label.active {
    fill: #333;
  }

  .val-label {
    font-size: 10px;
    fill: #666;
    font-family: system-ui, sans-serif;
    pointer-events: none;
  }
</style>
