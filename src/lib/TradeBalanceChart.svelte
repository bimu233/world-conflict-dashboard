<script>
  import * as d3 from 'd3';

  // tradePartners: [{partner_name, partner_iso3, total_usd, exports_usd, imports_usd}]
  // may be empty
  export let tradePartners = [];

  const width  = 560;
  const height = 210;
  const margin = { top: 24, right: 60, bottom: 15, left: 100 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  // Compute balance for each partner, then take top 8 sorted by abs(balance) desc
  $: withBalance = tradePartners.map(d => ({
    ...d,
    balance: (d.exports_usd ?? 0) - (d.imports_usd ?? 0)
  }));

  $: top8 = withBalance
    .slice()
    .sort((a, b) => Math.abs(b.balance) - Math.abs(a.balance))
    .slice(0, 8);

  $: maxAbs = d3.max(top8, d => Math.abs(d.balance)) || 1;

  $: yScale = d3.scaleBand()
    .domain(top8.map(d => d.partner_name))
    .range([0, iH])
    .padding(0.2);

  $: xScale = d3.scaleLinear()
    .domain([-maxAbs, maxAbs])
    .nice()
    .range([0, iW]);

  $: xTicks = xScale.ticks(4);

  function fmtUSD(v) {
    const abs = Math.abs(v);
    let str;
    if (abs >= 1_000_000_000) str = (abs / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
    else if (abs >= 1_000_000) str = (abs / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    else if (abs >= 1_000)     str = Math.round(abs / 1_000) + 'k';
    else                       str = String(Math.round(abs));
    return v < 0 ? '-' + str : str;
  }

  function fmtBalance(v) {
    const abs = Math.abs(v);
    let str;
    if (abs >= 1_000_000_000) str = (abs / 1_000_000_000).toFixed(1).replace(/\.0$/, '') + 'B';
    else if (abs >= 1_000_000) str = (abs / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    else if (abs >= 1_000)     str = Math.round(abs / 1_000) + 'k';
    else                       str = String(Math.round(abs));
    return v > 0 ? '+' + str : v < 0 ? '-' + str : str;
  }

  function truncate(name, max = 12) {
    return name && name.length > max ? name.slice(0, max - 1) + '…' : name;
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Trade Balance by Partner</span>
    <span class="subtitle-badge">(Exports − Imports)</span>
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

        <!-- zero line -->
        <line
          x1={xScale(0)} x2={xScale(0)}
          y1={0}          y2={iH}
          stroke="#ccc"
          stroke-width="1.5"
        />

        <!-- bars -->
        {#each top8 as d}
          {@const bh   = yScale.bandwidth()}
          {@const by   = yScale(d.partner_name)}
          {@const x0   = xScale(0)}
          {@const x1   = xScale(d.balance)}
          {@const bx   = Math.min(x0, x1)}
          {@const bw   = Math.abs(x1 - x0)}
          {@const fill = d.balance >= 0 ? 'rgba(41,128,185,0.8)' : 'rgba(192,57,43,0.8)'}

          <rect
            x={bx}
            y={by}
            width={bw}
            height={bh}
            fill={fill}
            rx="2"
          >
            <title>{d.partner_name}: {fmtBalance(d.balance)}</title>
          </rect>

          <!-- partner name label -->
          <text
            x={-6}
            y={by + bh / 2}
            class="bar-label active"
            text-anchor="end"
            dy="0.35em"
          >
            {truncate(d.partner_name)}
          </text>

          <!-- value label: outside bar tip for positive, inside near zero for negative -->
          <text
            x={d.balance >= 0 ? x1 + 4 : x0 - 4}
            y={by + bh / 2}
            class="val-label"
            text-anchor={d.balance >= 0 ? 'start' : 'end'}
            dy="0.35em"
          >
            {fmtBalance(d.balance)}
          </text>
        {/each}

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

  .subtitle-badge {
    font-size: 0.72rem;
    color: #888;
    background: #f0f0f0;
    border-radius: 4px;
    padding: 1px 5px;
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
    fill: #555;
    font-family: system-ui, sans-serif;
    pointer-events: none;
  }

  .empty-label {
    font-size: 12px;
    fill: #aaa;
    font-family: system-ui, sans-serif;
  }
</style>
