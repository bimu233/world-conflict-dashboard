<script>
  import * as d3 from 'd3';
  import { createEventDispatcher } from 'svelte';

  // rankData: [{country, gdp_growth}] sorted by gdp_growth desc, top+bottom combined
  export let rankData       = [];
  export let selectedCountry = '';
  export let metric         = 'gdp_growth';
  export let metricLabel    = 'GDP Growth %';

  const dispatch = createEventDispatcher();

  const width  = 340;
  const margin = { top: 8, right: 58, bottom: 8, left: 108 };
  const rowH   = 20;

  $: iW = width - margin.left - margin.right;
  $: height = rankData.length * rowH + margin.top + margin.bottom;

  $: xExtent = (() => {
    const vals = rankData.map(d => d[metric]);
    const lo = Math.min(d3.min(vals) ?? 0, 0);
    const hi = Math.max(d3.max(vals) ?? 0, 0);
    const pad = Math.max(Math.abs(hi), Math.abs(lo)) * 0.12 || 1;
    return [lo - pad, hi + pad];
  })();

  $: xScale = d3.scaleLinear().domain(xExtent).range([0, iW]);
  $: zeroX  = xScale(0);

  function fmtV(v) {
    if (v == null) return '';
    return (v >= 0 ? '+' : '') + v.toFixed(1) + '%';
  }
</script>

<div class="chart-box">
  <div class="chart-header">
    <span class="chart-title">Country/Region Ranking · {metricLabel}</span>
  </div>

  {#if !rankData.length}
    <p class="empty">No data available.</p>
  {:else}
    <svg viewBox="0 0 {width} {height}" style="width:100%;height:{height}px;display:block;">
      <g transform={`translate(${margin.left},${margin.top})`}>

        <!-- zero line -->
        <line x1={zeroX} x2={zeroX} y1={0} y2={height - margin.top - margin.bottom} class="zero-line" />

        {#each rankData as d, i}
          {@const y   = i * rowH}
          {@const val = d[metric]}
          {@const barX  = val >= 0 ? zeroX : xScale(val)}
          {@const barW  = Math.abs(xScale(val) - zeroX)}
          {@const isSel = d.country === selectedCountry}

          <rect
            x={barX} y={y + 3}
            width={barW} height={rowH - 6}
            fill={isSel ? '#e67e22' : val >= 0 ? 'rgba(39,174,96,0.55)' : 'rgba(192,57,43,0.55)'}
            style="cursor:pointer"
            on:click={() => dispatch('countrySelect', d.country)}
          />

          <!-- country label -->
          <text
            x={-4} y={y + rowH / 2}
            class="bar-label {isSel ? 'selected' : ''}"
            text-anchor="end" dy="0.35em"
            style="cursor:pointer"
            on:click={() => dispatch('countrySelect', d.country)}
          >{d.country}</text>

          <!-- value label: positive → outside right tip, negative → inside bar near zero -->
          <text
            x={val >= 0 ? xScale(val) + 3 : zeroX - 3}
            y={y + rowH / 2}
            class="val-label"
            text-anchor={val >= 0 ? 'start' : 'end'}
            dy="0.35em"
          >{fmtV(val)}</text>
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
    min-height: 100%;
  }
  .chart-header { margin-bottom: 4px; }
  .chart-title { font-size: 0.9rem; font-weight: 600; color: #222; }
  .empty { font-size: 0.82rem; color: #999; padding: 12px 0; text-align: center; margin: 0; }
  .zero-line { stroke: #bbb; stroke-width: 1; }
  .bar-label { font-size: 10px; fill: #444; font-family: system-ui, sans-serif; }
  .bar-label.selected { fill: #e67e22; font-weight: 700; }
  .val-label { font-size: 9px; fill: #666; font-family: system-ui, sans-serif; }
</style>
