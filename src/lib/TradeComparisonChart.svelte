<script>
  import * as d3 from 'd3';

  // comparisons: [{country, iso3, series: [{year, tradePct}]}]
  // selectedCountry: highlighted country name
  export let comparisons = [];
  export let selectedCountry = '';

  const width  = 440;
  const height = 220;
  const margin = { top: 24, right: 16, bottom: 32, left: 52 };
  const iW = width  - margin.left - margin.right;
  const iH = height - margin.top  - margin.bottom;

  $: allYears = [...new Set(comparisons.flatMap(c => c.series.map(d => d.year)))].sort((a, b) => a - b);

  $: xScale = d3.scaleLinear()
    .domain(allYears.length ? [allYears[0], allYears[allYears.length - 1]] : [1995, 2023])
    .range([0, iW]);

  $: allPcts = comparisons.flatMap(c => c.series.map(d => d.tradePct)).filter(v => v != null);
  $: yExtent = allPcts.length
    ? [Math.min(d3.min(allPcts), 0) * 1.1, Math.max(d3.max(allPcts), 0) * 1.1]
    : [-30, 30];
  $: yScale = d3.scaleLinear().domain(yExtent).nice().range([iH, 0]);

  $: zeroY = yScale(0);
  $: xTicks = xScale.ticks(6);
  $: yTicks = yScale.ticks(4);

  const peerColors = ['#3498db','#2ecc71','#9b59b6','#f39c12'];

  $: peerLines = comparisons.map((c, i) => {
    const isSelected = c.country === selectedCountry;
    return {
      ...c,
      color: isSelected ? '#c0392b' : peerColors[i % peerColors.length],
      strokeW: isSelected ? 2.5 : 1.2,
      opacity: isSelected ? 1 : 0.55,
      path: c.series.length >= 2
        ? d3.line()
            .defined(d => d.tradePct != null)
            .x(d => xScale(d.year))
            .y(d => yScale(d.tradePct))
            (c.series)
        : null,
    };
  // put selected country last so it renders on top
  }).sort((a, b) => (a.country === selectedCountry ? 1 : -1) - (b.country === selectedCountry ? 1 : -1));

  function fmtP(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Trade % Change — Regional Peers</span>
  </div>

  {#if comparisons.length === 0}
    <p class="empty">Select a country to compare with regional peers.</p>
  {:else}
    <svg {width} {height}>
      <g transform={`translate(${margin.left},${margin.top})`}>

        {#each yTicks as tick}
          <line x1={0} x2={iW} y1={yScale(tick)} y2={yScale(tick)} class="grid-line" />
          <text x={-6} y={yScale(tick)} class="axis-label" text-anchor="end" dy="0.35em">
            {fmtP(tick)}
          </text>
        {/each}

        {#each xTicks as tick}
          <text x={xScale(tick)} y={iH + 20} class="axis-label" text-anchor="middle">{tick}</text>
        {/each}
        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />

        {#if zeroY >= 0 && zeroY <= iH}
          <line x1={0} x2={iW} y1={zeroY} y2={zeroY} class="zero-line" />
        {/if}

        {#each peerLines as c}
          {#if c.path}
            <path
              d={c.path}
              fill="none"
              stroke={c.color}
              stroke-width={c.strokeW}
              opacity={c.opacity}
            >
              <title>{c.country}</title>
            </path>
          {/if}
        {/each}

        <!-- country name labels at end of line -->
        {#each peerLines as c}
          {#if c.series.length}
            {@const last = c.series[c.series.length - 1]}
            {#if last.tradePct != null}
              <text
                x={xScale(last.year) + 4}
                y={yScale(last.tradePct)}
                class="line-label"
                fill={c.color}
                opacity={c.opacity}
                dy="0.35em"
              >{c.country === selectedCountry ? c.country : ''}</text>
            {/if}
          {/if}
        {/each}

      </g>
    </svg>

    <!-- legend below chart -->
    <div class="legend">
      {#each peerLines as c}
        <span class="leg-item">
          <span class="leg-swatch" style="background:{c.color};opacity:{c.opacity}"></span>
          <span class="leg-name" style="color:{c.color};font-weight:{c.country === selectedCountry ? 600 : 400}">{c.country}</span>
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
  .grid-line { stroke: #eee; stroke-width: 1; }
  .zero-line { stroke: #bbb; stroke-width: 1; stroke-dasharray: 3,2; }
  .axis-line { stroke: #ccc; }
  .axis-label { font-size: 10px; fill: #666; font-family: system-ui, sans-serif; }
  .line-label { font-size: 9px; font-family: system-ui, sans-serif; }
  .empty { font-size: 0.82rem; color: #999; padding: 20px 0; text-align: center; }
  .legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    padding: 2px 4px 4px;
  }
  .leg-item { display: flex; align-items: center; gap: 4px; }
  .leg-swatch {
    display: inline-block;
    width: 16px; height: 3px;
    border-radius: 2px;
    flex-shrink: 0;
  }
  .leg-name { font-size: 0.70rem; }
</style>
