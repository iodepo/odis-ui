<script lang="ts">
  import { onMount } from "svelte";
  import { getNetworkStatus, type NetworkNodeStatus, type NetworkStatusResponse } from "./api";

  let status: NetworkStatusResponse | null = $state(null);
  let error: string | null = $state(null);
  let loading = $state(true);

  onMount(() => {
    void (async () => {
      loading = true;
      error = null;
      try {
        status = await getNetworkStatus();
      } catch (e) {
        error = e instanceof Error ? e.message : "Failed to load network status.";
      } finally {
        loading = false;
      }
    })();
  });

  function pct(part: number, whole: number): number {
    if (whole <= 0) return 0;
    return Math.min(100, Math.max(0, (part / whole) * 100));
  }
</script>

{#snippet nodeTable(nodes: NetworkNodeStatus[])}
  {#if nodes.length === 0}
    <p class="network-empty">None</p>
  {:else}
    <div class="network-table-wrap">
      <table class="network-table">
        <thead>
          <tr>
            <th scope="col">Name</th>
            <th scope="col">Errors</th>
          </tr>
        </thead>
        <tbody>
          {#each nodes as node (node.id)}
            <tr>
              <td>
                {#if node.url}
                  <a href={node.url} target="_blank" rel="noopener noreferrer">{node.name}</a>
                {:else}
                  {node.name}
                {/if}
              </td>
              <td>
                <ul class="network-errors">
                  {#each node.errors as msg, i (i)}
                    <li>{msg}</li>
                  {/each}
                </ul>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}
{/snippet}

<section class="network-page">
  <h1>ODIS network status</h1>
  <p class="network-lede">Status of the federated nodes of the ODIS network.</p>

  {#if loading}
    <p class="results-meta">Loading…</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else if status}
    {@const total = status.total_nodes}
    {@const errorsPct = pct(status.total_error_nodes, total)}
    {@const unresponsivePct = pct(status.unresponsive_count, total)}
    {@const parsingPct = pct(status.parsing_error_count, total)}
    {@const summonerPct = pct(status.summoner_error_count, total)}

    <h2>Summary</h2>
    <dl class="network-summary">
      <div>
        <dt>Total nodes</dt>
        <dd>{status.total_nodes}</dd>
      </div>
      <div>
        <dt>Reporting errors</dt>
        <dd>{status.total_error_nodes}</dd>
        <div
          class="network-stat-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={status.total_error_nodes}
          aria-label="{status.total_error_nodes} of {total} nodes reporting errors"
        >
          <span class="network-stat-bar-errors" style="width: {errorsPct}%"></span>
        </div>
      </div>
      <div>
        <dt>Unresponsive</dt>
        <dd>{status.unresponsive_count}</dd>
        <div
          class="network-stat-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={status.unresponsive_count}
          aria-label="{status.unresponsive_count} of {total} nodes unresponsive"
        >
          <span class="network-stat-bar-errors" style="width: {errorsPct}%"></span>
          <span class="network-stat-bar-subset" style="width: {unresponsivePct}%"></span>
        </div>
      </div>
      <div>
        <dt>with parsing errors</dt>
        <dd>{status.parsing_error_count}</dd>
        <div
          class="network-stat-bar"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={status.parsing_error_count}
          aria-label="{status.parsing_error_count} of {total} nodes with parsing errors"
        >
          <span class="network-stat-bar-errors" style="width: {errorsPct}%"></span>
          <span
            class="network-stat-bar-subset"
            style="left: {Math.max(0, errorsPct - parsingPct)}%; width: {parsingPct}%"
          ></span>
        </div>
      </div>
      {#if status.summoner_error_count > 0}
        <div>
          <dt>Summoner errors</dt>
          <dd>{status.summoner_error_count}</dd>
          <div
            class="network-stat-bar"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={total}
            aria-valuenow={status.summoner_error_count}
            aria-label="{status.summoner_error_count} of {total} nodes with summoner errors"
          >
            <span class="network-stat-bar-errors" style="width: {errorsPct}%"></span>
            <span class="network-stat-bar-subset" style="width: {summonerPct}%"></span>
          </div>
        </div>
      {/if}
    </dl>

    <h2>Unresponsive nodes ({status.unresponsive_count})</h2>
    {@render nodeTable(status.unresponsive)}

    <h2>Nodes with parsing errors ({status.parsing_error_count})</h2>
    {@render nodeTable(status.parsing_errors)}
  {/if}
</section>
