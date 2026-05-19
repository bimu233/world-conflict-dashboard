<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // yearData: [{year, deaths, low, high}] sorted by year
  export let yearData = [];
  export let selectedYear;
  export let filterLabel = '';

  const dispatch = createEventDispatcher();

  const width  = 580;
  const height = 188;
  const margin = { top: 24, right: 20, bottom: 32, left: 64 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  // y-domain uses the high estimate so the envelope never clips
  $: yMax = d3.max(yearData, d => d.high ?? d.deaths) || 1;

  $: xScale = d3.scaleLinear()
    .domain(yearData.length ? [d3.min(yearData, d => d.year), d3.max(yearData, d => d.year)] : [1989, 2024])
    .range([0, iW]);

  $: yScale = d3.scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([iH, 0]);

  // Shaded envelope between low and high estimates
  $: envelopePath = yearData.length >= 2
    ? d3.area()
        .x(d => xScale(d.year))
        .y0(d => yScale(d.low  ?? d.deaths))
        .y1(d => yScale(d.high ?? d.deaths))
        (yearData)
    : null;

  // Best-estimate line
  $: linePath = yearData.length >= 2
    ? d3.line().x(d => xScale(d.year)).y(d => yScale(d.deaths))(yearData)
    : null;

  $: xTicks = xScale.ticks(7);
  $: yTicks = yScale.ticks(4);

  function fmt(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1_000)     return Math.round(v / 1_000) + 'k';
    return String(v);
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Deaths Over Time</span>
    {#if filterLabel}<span class="filter-badge">{filterLabel}</span>{/if}
    <div class="legend">
      <span class="legend-band"></span><span class="legend-label">Low–High range</span>
      <span class="legend-line"></span><span class="legend-label">Best estimate</span>
    </div>
    <span class="hint">click a dot to set year</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      <!-- grid lines + y-axis labels -->
      {#each yTicks as tick}
        <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
        <text x={-8} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">
          {fmt(tick)}
        </text>
      {/each}

      <!-- x-axis labels -->
      {#each xTicks as tick}
        <text x={xScale(tick)} y={iH + 20} class="axis-label" text-anchor="middle">{tick}</text>
      {/each}
      <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />

      <!-- low–high envelope (drawn first so the line sits on top) -->
      {#if envelopePath}
        <path d={envelopePath} class="envelope" />
      {/if}

      <!-- best-estimate line -->
      {#if linePath}
        <path d={linePath} fill="none" stroke="#c0392b" stroke-width="2" />
      {/if}

      <!-- selected-year indicator -->
      {#if yearData.length}
        <line
          x1={xScale(selectedYear)} x2={xScale(selectedYear)}
          y1={0} y2={iH}
          stroke="#e67e22" stroke-width="1.5" stroke-dasharray="4,3"
        />
      {/if}

      <!-- dots — click sets year -->
      {#each yearData as d}
        <circle
          cx={xScale(d.year)} cy={yScale(d.deaths)}
          r={d.year === selectedYear ? 5 : 3}
          fill={d.year === selectedYear ? '#e67e22' : '#c0392b'}
          stroke="white" stroke-width="1"
          style="cursor:pointer"
          on:click={() => dispatch('yearSelect', d.year)}
        >
          <title>{d.year}: best {d.deaths.toLocaleString()} · low {(d.low ?? d.deaths).toLocaleString()} · high {(d.high ?? d.deaths).toLocaleString()}</title>
        </circle>
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

  .filter-badge {
    font-size: 0.75rem;
    background: #fdecea;
    color: #c0392b;
    border-radius: 4px;
    padding: 1px 6px;
  }

  .legend {
    display: flex;
    align-items: center;
    gap: 5px;
    margin-left: 4px;
  }

  .legend-band {
    display: inline-block;
    width: 18px;
    height: 8px;
    background: rgba(192, 57, 43, 0.18);
    border: 1px solid rgba(192, 57, 43, 0.35);
    border-radius: 2px;
    flex-shrink: 0;
  }

  .legend-line {
    display: inline-block;
    width: 18px;
    height: 2px;
    background: #c0392b;
    flex-shrink: 0;
  }

  .legend-label {
    font-size: 0.70rem;
    color: #888;
  }

  .hint {
    font-size: 0.72rem;
    color: #aaa;
    margin-left: auto;
  }

  .envelope {
    fill: rgba(192, 57, 43, 0.12);
    stroke: rgba(192, 57, 43, 0.30);
    stroke-width: 1;
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
</style>
