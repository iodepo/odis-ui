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
    <h2>Summary</h2>
    <dl class="network-summary">
      <div>
        <dt>Total nodes</dt>
        <dd>{status.total_nodes}</dd>
      </div>
      <div>
        <dt>Reporting errors</dt>
        <dd>{status.total_error_nodes}</dd>
      </div>
      <div>
        <dt>Unresponsive</dt>
        <dd>{status.unresponsive_count}</dd>
      </div>
      <div>
        <dt>Parsing errors</dt>
        <dd>{status.parsing_error_count}</dd>
      </div>
      {#if status.summoner_error_count > 0}
        <div>
          <dt>Summoner errors</dt>
          <dd>{status.summoner_error_count}</dd>
        </div>
      {/if}
    </dl>

    <h2>Unresponsive nodes ({status.unresponsive_count})</h2>
    {@render nodeTable(status.unresponsive)}

    <h2>Nodes with parsing errors ({status.parsing_error_count})</h2>
    {@render nodeTable(status.parsing_errors)}
  {/if}
</section>
