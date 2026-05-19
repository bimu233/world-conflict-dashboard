<script>
  import * as d3 from 'd3';

  export let pcts            = [];   // [{country, tradePct}]
  export let selectedPct     = null;
  export let gdpPcts         = [];   // [{country, gdpGrowth}]
  export let selectedGdpPct  = null;
  export let selectedCountry = '';
  export let year            = null;

  const width  = 480;
  const cH     = 200;
  const margin = { top: 28, right: 20, bottom: 38, left: 44 };
  const iW = width - margin.left - margin.right;
  const iH = cH   - margin.top  - margin.bottom;

  // ── shared KDE helpers ────────────────────────────────────────────────────
  function gaussianKernel(bw) {
    return x => Math.exp(-0.5 * (x / bw) ** 2) / (bw * Math.sqrt(2 * Math.PI));
  }

  function silverman(vals) {
    if (vals.length < 2) return 5;
    const m  = d3.mean(vals);
    const sd = Math.sqrt(d3.mean(vals.map(v => (v - m) ** 2)));
    return 1.06 * sd * Math.pow(vals.length, -0.2) || 3;
  }

  function buildKde(vals, extent) {
    if (vals.length < 3) return { kdePoints: [], areaPath: null, curvePath: null, xScale: null, yScale: null, xTicks: [] };
    const bw     = silverman(vals);
    const kernel = gaussianKernel(bw);
    const step   = (extent[1] - extent[0]) / 200;
    const pts    = d3.range(extent[0], extent[1], step)
                     .map(x => ({ x, y: d3.mean(vals, v => kernel(x - v)) }));

    const xScale = d3.scaleLinear().domain(extent).range([0, iW]);
    const yMax   = d3.max(pts, d => d.y) || 1;
    const yScale = d3.scaleLinear().domain([0, yMax]).range([iH, 0]);

    const line = d3.line().x(d => xScale(d.x)).y(d => yScale(d.y)).curve(d3.curveBasis);
    const area = d3.area().x(d => xScale(d.x)).y0(iH).y1(d => yScale(d.y)).curve(d3.curveBasis);

    return {
      kdePoints: pts,
      curvePath: line(pts),
      areaPath:  area(pts),
      xScale,
      yScale,
      xTicks: xScale.ticks(5),
    };
  }

  function xExtentFor(vals) {
    const lo = d3.min(vals), hi = d3.max(vals);
    const pad = (hi - lo) * 0.12 || 10;
    return [lo - pad, hi + pad];
  }

  function pctile(vals, v) {
    return Math.round((vals.filter(x => x <= v).length / vals.length) * 100);
  }

  // ── trade KDE ─────────────────────────────────────────────────────────────
  $: tradeVals   = pcts.map(d => d.tradePct).filter(v => v != null && isFinite(v));
  $: tradeExtent = tradeVals.length ? xExtentFor(tradeVals) : [-50, 50];
  $: tradeKde    = buildKde(tradeVals, tradeExtent);
  $: tradePctile = selectedPct != null && tradeVals.length ? pctile(tradeVals, selectedPct) : null;

  // ── GDP KDE ───────────────────────────────────────────────────────────────
  $: gdpVals    = gdpPcts.map(d => d.gdpGrowth).filter(v => v != null && isFinite(v));
  $: gdpExtent  = gdpVals.length ? xExtentFor(gdpVals) : [-10, 10];
  $: gdpKde     = buildKde(gdpVals, gdpExtent);
  $: gdpPctile  = selectedGdpPct != null && gdpVals.length ? pctile(gdpVals, selectedGdpPct) : null;

  // ── helpers ───────────────────────────────────────────────────────────────
  function fmtP(v) { return (v >= 0 ? '+' : '') + v.toFixed(1) + '%'; }
  function ordinal(n) {
    const s = ['th','st','nd','rd'], v = n % 100;
    return n + (s[(v - 20) % 10] ?? s[v] ?? s[0]);
  }
  function anchor(val, extent) {
    return val > (extent[0] + extent[1]) / 2 ? 'end' : 'start';
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Distributions</span>
    {#if year}<span class="year-badge">{year}</span>{/if}
  </div>
  <div class="sub">All countries with data</div>

  <!-- Trade % Change KDE -->
  <div class="sub-title">Trade % Change</div>
  {#if tradeVals.length < 3}
    <p class="empty">Not enough trade data for {year}.</p>
  {:else}
    <svg {width} height={cH} overflow="visible">
      <g transform={`translate(${margin.left},${margin.top})`}>
        {#if tradeKde.areaPath}<path d={tradeKde.areaPath} class="area trade-area" />{/if}
        {#if tradeKde.curvePath}<path d={tradeKde.curvePath} class="curve trade-curve" />{/if}

        {#if selectedPct != null}
          {@const sx = tradeKde.xScale(selectedPct)}
          {@const anc = anchor(selectedPct, tradeExtent)}
          <line x1={sx} x2={sx} y1={0} y2={iH} class="sel-line" />
          <text x={sx} y={-20} class="sel-label" text-anchor={anc}>{selectedCountry}  {fmtP(selectedPct)}</text>
          {#if tradePctile != null}
            <text x={sx} y={-8} class="pct-label" text-anchor={anc}>{ordinal(tradePctile)} percentile</text>
          {/if}
        {/if}

        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />
        {#each tradeKde.xTicks as tick}
          <text x={tradeKde.xScale(tick)} y={iH + 18} class="axis-label" text-anchor="middle">{fmtP(tick)}</text>
        {/each}
        {#if tradeExtent[0] < 0 && tradeExtent[1] > 0}
          <line x1={tradeKde.xScale(0)} x2={tradeKde.xScale(0)} y1={0} y2={iH} class="zero-line" />
        {/if}
        <text x={iW / 2} y={iH + 30} class="axis-title" text-anchor="middle">Trade % Change</text>
      </g>
    </svg>
    <div class="count-note">{tradeVals.length} countries</div>
  {/if}

  <div class="divider"></div>

  <!-- GDP Growth KDE -->
  <div class="sub-title">GDP Growth %</div>
  {#if gdpVals.length < 3}
    <p class="empty">Not enough GDP data for {year}.</p>
  {:else}
    <svg {width} height={cH} overflow="visible">
      <g transform={`translate(${margin.left},${margin.top})`}>
        {#if gdpKde.areaPath}<path d={gdpKde.areaPath} class="area gdp-area" />{/if}
        {#if gdpKde.curvePath}<path d={gdpKde.curvePath} class="curve gdp-curve" />{/if}

        {#if selectedGdpPct != null}
          {@const sx = gdpKde.xScale(selectedGdpPct)}
          {@const anc = anchor(selectedGdpPct, gdpExtent)}
          <line x1={sx} x2={sx} y1={0} y2={iH} class="sel-line" />
          <text x={sx} y={-20} class="sel-label" text-anchor={anc}>{selectedCountry}  {fmtP(selectedGdpPct)}</text>
          {#if gdpPctile != null}
            <text x={sx} y={-8} class="pct-label" text-anchor={anc}>{ordinal(gdpPctile)} percentile</text>
          {/if}
        {/if}

        <line x1={0} x2={iW} y1={iH} y2={iH} class="axis-line" />
        {#each gdpKde.xTicks as tick}
          <text x={gdpKde.xScale(tick)} y={iH + 18} class="axis-label" text-anchor="middle">{fmtP(tick)}</text>
        {/each}
        {#if gdpExtent[0] < 0 && gdpExtent[1] > 0}
          <line x1={gdpKde.xScale(0)} x2={gdpKde.xScale(0)} y1={0} y2={iH} class="zero-line" />
        {/if}
        <text x={iW / 2} y={iH + 30} class="axis-title" text-anchor="middle">GDP Growth %</text>
      </g>
    </svg>
    <div class="count-note">{gdpVals.length} countries</div>
  {/if}
</div>

<style>
  .chart-box {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 10px 12px 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    height: 100%;
    box-sizing: border-box;
  }
  .chart-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 1px; }
  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }
  .year-badge {
    font-size: 0.75rem;
    background: #eaf4fb;
    color: #2980b9;
    border-radius: 4px;
    padding: 1px 6px;
  }
  .sub { font-size: 0.70rem; color: #aaa; margin-bottom: 4px; }
  .sub-title { font-size: 0.75rem; font-weight: 600; color: #555; margin: 6px 0 0; }
  .divider { border-top: 1px solid #eee; margin: 8px 0 4px; }
  .empty { font-size: 0.82rem; color: #999; padding: 12px 0; text-align: center; margin: 0; }
  .count-note { font-size: 0.68rem; color: #bbb; text-align: right; padding: 0 4px 2px; }

  .trade-area { fill: rgba(41,128,185,0.12); }
  .trade-curve { fill: none; stroke: #2980b9; stroke-width: 2; }
  .gdp-area { fill: rgba(39,174,96,0.12); }
  .gdp-curve { fill: none; stroke: #27ae60; stroke-width: 2; }

  .sel-line { stroke: #e67e22; stroke-width: 1.5; stroke-dasharray: 4,3; }
  .sel-label { font-size: 9px; fill: #e67e22; font-family: system-ui, sans-serif; font-weight: 600; }
  .pct-label { font-size: 9px; fill: #e67e22; font-family: system-ui, sans-serif; opacity: 0.85; }
  .zero-line { stroke: #ccc; stroke-width: 1; stroke-dasharray: 3,2; }
  .axis-line { stroke: #ccc; }
  .axis-label { font-size: 10px; fill: #666; font-family: system-ui, sans-serif; }
  .axis-title { font-size: 9px; fill: #888; font-family: system-ui, sans-serif; }
</style>
