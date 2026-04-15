<script>
  import * as d3 from "d3";
  import { createEventDispatcher } from "svelte";
  import { csvToGeo, geoNameToCSV } from "./nameMap.js";

  export let geoData;
  export let data;               // [{country, region, deaths}] for current year
  export let selectedCountry = null;
  export let selectedRegion  = null;

  const dispatch = createEventDispatcher();

  let width = 960;
  let height = 500;

  // Current zoom transform (string applied to the <g> element)
  let transform = "";

  // Hold a reference to the d3 zoom so buttons can call it
  let zoomBehavior;
  let svgEl;

  // projection + path
  const projection = d3.geoNaturalEarth1();
  const path = d3.geoPath(projection);

  $: if (geoData) {
    projection.fitSize([width, height], geoData);
  }

  // geoName → {deaths, region}
  $: deathMap = new Map(
    (data || []).map(d => [csvToGeo(d.country), { deaths: d.deaths, region: d.region }])
  );

  $: maxVal = d3.max(data || [], d => d.deaths) || 1;

  // When a region is selected, countries outside it are dimmed to grey.
  function getColor(feature, map, max, region) {
    const entry = map.get(feature.properties.name);
    if (!entry) return "#eee";
    if (region && entry.region !== region) return "#ddd";
    return d3.interpolateReds(entry.deaths / max);
  }

  function handleClick(feature) {
    dispatch("countryClick", geoNameToCSV(feature.properties.name));
  }

  // Legend config
  const legendW = 180;
  const legendH = 10;
  const legendX = 16;
  const legendY = height - 48;

  // Gradient stops: 6 evenly spaced samples of the Reds scale
  const stops = [0, 0.2, 0.4, 0.6, 0.8, 1].map(t => ({
    offset: `${t * 100}%`,
    color: t === 0 ? "#eee" : d3.interpolateReds(t),
  }));

  // Tick positions and labels (0, 25%, 50%, 75%, max)
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  function fmtDeaths(v) {
    if (v >= 1_000_000) return (v / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
    if (v >= 1_000)     return Math.round(v / 1_000) + "k";
    return String(v);
  }

  // Svelte action: attach d3.zoom to the SVG element
  function zoomAction(node) {
    svgEl = node;
    zoomBehavior = d3.zoom()
      .scaleExtent([1, 12])
      .on("zoom", (event) => {
        transform = event.transform.toString();
      });

    d3.select(node).call(zoomBehavior);

    return {
      destroy() {
        d3.select(node).on(".zoom", null);
      }
    };
  }

  function zoomIn() {
    d3.select(svgEl).transition().duration(300).call(zoomBehavior.scaleBy, 1.5);
  }

  function zoomOut() {
    d3.select(svgEl).transition().duration(300).call(zoomBehavior.scaleBy, 1 / 1.5);
  }

  function resetZoom() {
    d3.select(svgEl).transition().duration(400).call(zoomBehavior.transform, d3.zoomIdentity);
  }
</script>

<div class="map-container">
  <svg {width} {height} use:zoomAction>
    <g transform={transform}>
      {#if geoData}
        {#each geoData.features as f}
          <path
            d={path(f)}
            fill={getColor(f, deathMap, maxVal, selectedRegion)}
            stroke={geoNameToCSV(f.properties.name) === selectedCountry ? "#e67e22" : "#ccc"}
            stroke-width={geoNameToCSV(f.properties.name) === selectedCountry ? 2 : 0.5}
            style="cursor: pointer;"
            on:click={() => handleClick(f)}
          />
        {/each}
      {/if}
    </g>

    <!-- Legend — fixed in SVG space, unaffected by zoom -->
    <defs>
      <linearGradient id="legend-gradient" x1="0%" x2="100%" y1="0%" y2="0%">
        {#each stops as s}
          <stop offset={s.offset} stop-color={s.color} />
        {/each}
      </linearGradient>
    </defs>

    <g class="legend">
      <rect
        x={legendX} y={legendY}
        width={legendW} height={legendH}
        rx="2"
        fill="url(#legend-gradient)"
        stroke="#bbb" stroke-width="0.5"
      />
      {#each ticks as t}
        <line
          x1={legendX + t * legendW} x2={legendX + t * legendW}
          y1={legendY + legendH} y2={legendY + legendH + 4}
          stroke="#666" stroke-width="1"
        />
        <text
          x={legendX + t * legendW}
          y={legendY + legendH + 14}
          class="legend-tick"
          text-anchor={t === 0 ? "start" : t === 1 ? "end" : "middle"}
        >
          {fmtDeaths(Math.round(t * maxVal))}
        </text>
      {/each}
      <text x={legendX} y={legendY - 8} class="legend-title">Deaths (best estimate)</text>
    </g>
  </svg>

  <div class="zoom-controls">
    <button on:click={zoomIn}  title="Zoom in">+</button>
    <button on:click={resetZoom} title="Reset zoom">⌂</button>
    <button on:click={zoomOut} title="Zoom out">−</button>
  </div>
</div>

<style>
  .map-container {
    position: relative;
    display: inline-block;
  }

  svg {
    display: block;
    background: #f0f4f8;
    border-radius: 6px;
  }

  .zoom-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .zoom-controls button {
    width: 30px;
    height: 30px;
    font-size: 1.1rem;
    line-height: 1;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
  }

  .zoom-controls button:hover {
    background: #f5f5f5;
  }

  .legend-title {
    font-size: 11px;
    fill: #444;
    font-family: system-ui, sans-serif;
  }

  .legend-tick {
    font-size: 10px;
    fill: #555;
    font-family: system-ui, sans-serif;
  }
</style>
