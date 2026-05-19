<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // tradePartners: [{partner_name, partner_iso3, total_usd, exports_usd, imports_usd}]
  // sorted by total_usd desc, may be empty
  export let tradePartners = [];
  export let selectedCountry = null;

  const dispatch = createEventDispatcher();

  const width  = 480;
  const height = 210;
  const margin = { top: 24, right: 20, bottom: 15, left: 90 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: top8 = tradePartners.slice(0, 8);

  $: yScale = d3.scaleBand()
    .domain(top8.map(d => d.partner_name))
    .range([0, iH])
    .padding(0.2);

  $: xMax = d3.max(top8, d => d.total_usd) || 1;

  $: xScale = d3.scaleLinear()
    .domain([0, xMax])
    .range([0, iW]);

  $: xTicks = xScale.ticks(4);

  function fmtUSD(v) {
    const abs = Math.abs(v);
    if (abs >= 1_000_000_000) return (v / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
    if (abs >= 1_000_000)     return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (abs >= 1_000)         return Math.round(v / 1_000) + 'k';
    return String(Math.round(v));
  }

  function truncate(name, max = 12) {
    return name && name.length > max ? name.slice(0, max - 1) + '…' : name;
  }

  function select(partner_name) {
    dispatch('countrySelect', partner_name);
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Top Trading Partners</span>
    <span class="hint">click to select</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      {#if top8.length === 0}
        <text
          x={iW / 2}
          y={iH / 2}
          text-anchor="middle"
          dy="0.35em"
          class="empty-label"
        >Select a country on the map</text>
      {:else}

        <!-- grid lines + x axis labels -->
        {#each xTicks as tick}
          <line x1={xScale(tick)} x2={xScale(tick)} y1={0} y2={iH} class="grid-line" />
          <text x={xScale(tick)} y={iH + 14} class="axis-label" text-anchor="middle">{fmtUSD(tick)}</text>
        {/each}

        <!-- bars -->
        {#each top8 as d}
          {@const exportsVal = d.exports_usd ?? 0}
          {@const importsVal = d.imports_usd ?? 0}
          {@const totalVal   = d.total_usd   ?? 0}
          {@const isSelected = d.partner_name === selectedCountry}
          {@const exportsFill = isSelected ? 'rgba(41,128,185,1)' : 'rgba(41,128,185,0.75)'}
          {@const importsFill = isSelected ? 'rgba(230,126,34,1)' : 'rgba(230,126,34,0.75)'}
          {@const bh = yScale.bandwidth()}
          {@const by = yScale(d.partner_name)}

          <!-- exports segment -->
          <rect
            x={0}
            y={by}
            width={xScale(exportsVal)}
            height={bh}
            fill={exportsFill}
            rx="2"
            style="cursor:pointer"
            on:click={() => select(d.partner_name)}
          >
            <title>{d.partner_name} — Exports: {fmtUSD(exportsVal)}</title>
          </rect>

          <!-- imports segment -->
          <rect
            x={xScale(exportsVal)}
            y={by}
            width={xScale(importsVal)}
            height={bh}
            fill={importsFill}
            rx="2"
            style="cursor:pointer"
            on:click={() => select(d.partner_name)}
          >
            <title>{d.partner_name} — Imports: {fmtUSD(importsVal)}</title>
          </rect>

          <!-- partner name label -->
          <text
            x={-6}
            y={by + bh / 2}
            class="bar-label"
            class:active={isSelected}
            text-anchor="end"
            dy="0.35em"
            style="cursor:pointer"
            on:click={() => select(d.partner_name)}
          >
            {truncate(d.partner_name)}
          </text>

          <!-- total value label after bar -->
          <text
            x={xScale(totalVal) + 4}
            y={by + bh / 2}
            class="val-label"
            dy="0.35em"
          >
            {fmtUSD(totalVal)}
          </text>
        {/each}

        <!-- Legend (top-right inside chart area) -->
        {@const lx = iW - 90}
        {@const ly = -18}
        <rect x={lx}      y={ly} width={10} height={10} fill="rgba(41,128,185,0.75)" rx="1" />
        <text x={lx + 13} y={ly + 9} class="legend-label">Exports</text>
        <rect x={lx + 55} y={ly} width={10} height={10} fill="rgba(230,126,34,0.75)" rx="1" />
        <text x={lx + 68} y={ly + 9} class="legend-label">Imports</text>

      {/if}
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
    font-weight: 600;
  }

  .val-label {
    font-size: 10px;
    fill: #666;
    font-family: system-ui, sans-serif;
    pointer-events: none;
  }

  .legend-label {
    font-size: 10px;
    fill: #555;
    font-family: system-ui, sans-serif;
  }

  .empty-label {
    font-size: 12px;
    fill: #aaa;
    font-family: system-ui, sans-serif;
  }
</style>
