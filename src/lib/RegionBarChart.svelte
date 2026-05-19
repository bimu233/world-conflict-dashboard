<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // regionData: [{region, deaths}] sorted by deaths desc
  export let regionData = [];
  export let selectedRegion = null;

  const dispatch = createEventDispatcher();

  const width  = 440;
  const height = 210;
  const margin = { top: 24, right: 24, bottom: 15, left: 90 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: yScale = d3.scaleBand()
    .domain(regionData.map(d => d.region))
    .range([0, iH])
    .padding(0.25);

  $: xScale = d3.scaleLinear()
    .domain([0, d3.max(regionData, d => d.deaths) || 1])
    .nice()
    .range([0, iW]);

  $: xTicks = xScale.ticks(4);

  function fmt(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1_000)     return Math.round(v / 1_000) + 'k';
    return String(v);
  }

  function toggle(region) {
    dispatch('regionSelect', selectedRegion === region ? null : region);
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Deaths by Region</span>
    <span class="hint">click to filter</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      <!-- grid lines + x labels -->
      {#each xTicks as tick}
        <line x1={xScale(tick)} x2={xScale(tick)} y1={0} y2={iH} class="grid-line" />
        <text x={xScale(tick)} y={iH + 14} class="axis-label" text-anchor="middle">{fmt(tick)}</text>
      {/each}

      <!-- bars -->
      {#each regionData as d}
        {@const active = selectedRegion === null || selectedRegion === d.region}
        <rect
          x={0}
          y={yScale(d.region)}
          width={xScale(d.deaths)}
          height={yScale.bandwidth()}
          fill={selectedRegion === d.region ? '#c0392b' : active ? '#e88080' : '#ddd'}
          rx="2"
          style="cursor:pointer"
          on:click={() => toggle(d.region)}
        >
          <title>{d.region}: {d.deaths.toLocaleString()} deaths</title>
        </rect>

        <!-- region label -->
        <text
          x={-6}
          y={yScale(d.region) + yScale.bandwidth() / 2}
          class="bar-label"
          class:active={active}
          text-anchor="end"
          dy="0.35em"
          style="cursor:pointer"
          on:click={() => toggle(d.region)}
        >
          {d.region}
        </text>

        <!-- value label inside bar -->
        {#if xScale(d.deaths) > 36}
          <text
            x={xScale(d.deaths) - 4}
            y={yScale(d.region) + yScale.bandwidth() / 2}
            class="val-label"
            text-anchor="end"
            dy="0.35em"
          >
            {fmt(d.deaths)}
          </text>
        {/if}
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
    fill: white;
    font-family: system-ui, sans-serif;
    pointer-events: none;
  }
</style>
