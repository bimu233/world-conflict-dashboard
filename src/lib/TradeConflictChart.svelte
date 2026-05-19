<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // series: [{year, deaths, tradePct}] — tradePct is % change in total trade vs prev year
  export let series = [];
  export let selectedYear;
  export let filterLabel = '';

  const dispatch = createEventDispatcher();

  const width  = 560;
  const height = 140;
  const margin = { top: 24, right: 60, bottom: 32, left: 64 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: validSeries = series.filter(d => d.deaths != null || d.tradePct != null);

  $: xScale = d3.scaleLinear()
    .domain(validSeries.length ? [d3.min(validSeries, d => d.year), d3.max(validSeries, d => d.year)] : [1995, 2023])
    .range([0, iW]);

  $: yDeathMax = d3.max(validSeries, d => d.deaths ?? 0) || 1;
  $: yDeathScale = d3.scaleLinear().domain([0, yDeathMax]).nice().range([iH, 0]);

  $: tradePctExtent = (() => {
    const vals = validSeries.filter(d => d.tradePct != null).map(d => d.tradePct);
    if (!vals.length) return [-20, 20];
    const lo = Math.min(d3.min(vals), 0);
    const hi = Math.max(d3.max(vals), 0);
    return [lo * 1.1, hi * 1.1];
  })();
  $: yTradeScale = d3.scaleLinear().domain(tradePctExtent).nice().range([iH, 0]);

  $: barWidth = validSeries.length > 1 ? Math.max(2, iW / validSeries.length - 1) : 8;

  $: tradeLine = validSeries.filter(d => d.tradePct != null).length >= 2
    ? d3.line()
        .defined(d => d.tradePct != null)
        .x(d => xScale(d.year))
        .y(d => yTradeScale(d.tradePct))
        (validSeries)
    : null;

  $: xTicks = xScale.ticks(7);
  $: yDeathTicks = yDeathScale.ticks(4);
  $: yTradeTicks = yTradeScale.ticks(4);

  $: zeroY = yTradeScale(0);

  function fmtD(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M';
    if (v >= 1_000)     return Math.round(v / 1_000) + 'k';
    return String(v);
  }
  function fmtP(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Deaths vs Trade Change</span>
    {#if filterLabel}<span class="filter-badge">{filterLabel}</span>{/if}
    <div class="legend">
      <span class="leg-bar"></span><span class="leg-lbl">Deaths (left)</span>
      <span class="leg-line"></span><span class="leg-lbl">Trade % chg (right)</span>
    </div>
    <span class="hint">click to set year</span>
  </div>

  <svg {width} {height}>
    <g transform={`translate(${margin.left},${margin.top})`}>

      <!-- left y-axis grid + labels (deaths) -->
      {#each yDeathTicks as tick}
        <line x1={0} x2={iW} y1={yDeathScale(tick)} y2={yDeathScale(tick)} class="grid-line" />
        <text x={-8} y={yDeathScale(tick)} class="axis-label left-label" text-anchor="end" dy="0.35em">
          {fmtD(tick)}
        </text>
      {/each}

      <!-- right y-axis labels (trade %) -->
      {#each yTradeTicks as tick}
        <text x={iW + 8} y={yTradeScale(tick)} class="axis-label right-label" text-anchor="start" dy="0.35em">
          {fmtP(tick)}
        </text>
      {/each}

      <!-- x-axis labels -->
      {#each xTicks as tick}
        <text x={xScale(tick)} y={iH + 20} class="axis-label" text-anchor="middle">{tick}</text>
      {/each}
      <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />

      <!-- zero reference for trade % -->
      {#if zeroY >= 0 && zeroY <= iH}
        <line x1={0} x2={iW} y1={zeroY} y2={zeroY} class="zero-line" />
      {/if}

      <!-- death bars -->
      {#each validSeries as d}
        {#if d.deaths != null}
          <rect
            x={xScale(d.year) - barWidth / 2}
            y={yDeathScale(d.deaths)}
            width={barWidth}
            height={iH - yDeathScale(d.deaths)}
            fill={d.year === selectedYear ? '#e74c3c' : 'rgba(192,57,43,0.35)'}
            style="cursor:pointer"
            on:click={() => dispatch('yearSelect', d.year)}
          >
            <title>{d.year}: {d.deaths.toLocaleString()} deaths · trade {d.tradePct != null ? fmtP(d.tradePct) : 'n/a'}</title>
          </rect>
        {/if}
      {/each}

      <!-- trade % line -->
      {#if tradeLine}
        <path d={tradeLine} fill="none" stroke="#2980b9" stroke-width="2" />
      {/if}

      <!-- trade dots -->
      {#each validSeries as d}
        {#if d.tradePct != null}
          <circle
            cx={xScale(d.year)} cy={yTradeScale(d.tradePct)}
            r={d.year === selectedYear ? 4 : 2.5}
            fill={d.year === selectedYear ? '#e67e22' : '#2980b9'}
            stroke="white" stroke-width="1"
            style="cursor:pointer"
            on:click={() => dispatch('yearSelect', d.year)}
          >
            <title>{d.year}: trade {fmtP(d.tradePct)}</title>
          </circle>
        {/if}
      {/each}

      <!-- selected-year indicator -->
      {#if validSeries.length}
        <line
          x1={xScale(selectedYear)} x2={xScale(selectedYear)}
          y1={0} y2={iH}
          stroke="#e67e22" stroke-width="1.5" stroke-dasharray="4,3"
        />
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
    flex-wrap: wrap;
  }
  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }
  .filter-badge {
    font-size: 0.75rem;
    background: #fdecea;
    color: #c0392b;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .legend { display: flex; align-items: center; gap: 5px; margin-left: 4px; }
  .leg-bar {
    display: inline-block;
    width: 12px; height: 10px;
    background: rgba(192,57,43,0.5);
    flex-shrink: 0;
  }
  .leg-line {
    display: inline-block;
    width: 18px; height: 2px;
    background: #2980b9;
    flex-shrink: 0;
  }
  .leg-lbl { font-size: 0.70rem; color: #888; }
  .hint { font-size: 0.72rem; color: #aaa; margin-left: auto; }
  .grid-line { stroke: #eee; stroke-width: 1; }
  .zero-line { stroke: #bbb; stroke-width: 1; stroke-dasharray: 3,2; }
  .axis-line { stroke: #ccc; }
  .axis-label { font-size: 10px; fill: #666; font-family: system-ui, sans-serif; }
  .left-label { fill: #c0392b; }
  .right-label { fill: #2980b9; }
</style>
