<script>
  import { createEventDispatcher } from 'svelte';
  export let country;
  export let year;
  export let conflicts; // [{conflict_name, side_a, side_b, deaths_a, deaths_b, best}]

  const dispatch = createEventDispatcher();

  $: totalDeaths = conflicts.reduce((sum, c) => sum + c.best, 0);
</script>

<div class="panel">
  <div class="panel-header">
    <div>
      <h2>{country}</h2>
      <span class="year-badge">{year}</span>
    </div>
    <button class="close-btn" on:click={() => dispatch('close')}>✕</button>
  </div>

  <p class="subtitle">
    <span class="total">{totalDeaths.toLocaleString()} total deaths</span>
    &nbsp;·&nbsp;
    {conflicts.length} conflict{conflicts.length !== 1 ? 's' : ''} recorded
  </p>

  <div class="legend">
    <span><strong>Side A Deaths:</strong> Best estimate of deaths sustained by Side A.</span>
    <span><strong>Side B Deaths:</strong> Best estimate of deaths sustained by Side B.</span>
    <span><strong>Best:</strong> Most likely estimate of total fatalities from an event — always the sum of deaths_a, deaths_b, deaths_civilians and deaths_unknown.</span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Side A</th>
          <th>Side B</th>
          <th class="num">Side A Deaths</th>
          <th class="num">Side B Deaths</th>
          <th class="num">Best</th>
        </tr>
      </thead>
      <tbody>
        {#each conflicts as c}
          <tr>
            <td>{c.side_a}</td>
            <td>{c.side_b}</td>
            <td class="num">{c.deaths_a.toLocaleString()}</td>
            <td class="num">{c.deaths_b.toLocaleString()}</td>
            <td class="num best">{c.best.toLocaleString()}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .panel {
    background: #fff;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    width: 100%;
    max-height: 466px;
    overflow-y: auto;
    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 4px;
  }

  h2 {
    margin: 0;
    font-size: 1.2rem;
  }

  .year-badge {
    font-size: 0.85rem;
    background: #eee;
    border-radius: 4px;
    padding: 2px 8px;
    color: #555;
  }

  .subtitle {
    margin: 4px 0 8px;
    font-size: 0.85rem;
    color: #666;
  }

  .total {
    font-weight: 600;
    color: #c0392b;
  }

  .legend {
    display: flex;
    flex-direction: column;
    gap: 3px;
    margin-bottom: 10px;
    padding: 8px 10px;
    background: #f9f9f9;
    border-radius: 4px;
    border-left: 3px solid #ddd;
    font-size: 0.78rem;
    color: #555;
    line-height: 1.4;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 1rem;
    cursor: pointer;
    color: #888;
    padding: 2px 6px;
  }
  .close-btn:hover { color: #000; }

  .table-wrap {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }

  th {
    text-align: left;
    padding: 6px 8px;
    background: #f5f5f5;
    border-bottom: 2px solid #ddd;
    white-space: nowrap;
  }

  td {
    padding: 5px 8px;
    border-bottom: 1px solid #eee;
    vertical-align: top;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #fafafa; }

  .num {
    text-align: right;
  }

  .best {
    font-weight: 600;
    color: #c0392b;
  }
</style>
