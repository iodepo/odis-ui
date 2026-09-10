<script lang="ts">
  import RelatedRecordsGraph from "./RelatedRecordsGraph.svelte";
  import ResultCard from "./ResultCard.svelte";
  import { getRecord, search, type SearchItem } from "./api";
  import { extractRelatedIds } from "./jsonldIds";

  type Props = {
    open: boolean;
    item: SearchItem;
    onClose: () => void;
  };

  let { open, item, onClose }: Props = $props();

  let dialogEl: HTMLDialogElement | undefined = $state();
  let loading = $state(false);
  let error = $state<string | null>(null);
  let scannedIds = $state(0);
  let related = $state<SearchItem[]>([]);
  let loadToken = 0;

  $effect(() => {
    const dialog = dialogEl;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  });

  $effect(() => {
    if (!open) return;
    const token = ++loadToken;
    const recordId = item.id;
    void loadRelated(token, recordId);
  });

  async function loadRelated(token: number, recordId: string) {
    loading = true;
    error = null;
    related = [];
    scannedIds = 0;

    try {
      const record = await getRecord(recordId, true);
      if (token !== loadToken) return;

      const selfUri =
        typeof record.raw?.id === "string" ? record.raw.id : null;
      const ids = extractRelatedIds(record.raw, selfUri);
      scannedIds = ids.length;

      if (ids.length === 0) {
        related = [];
        return;
      }

      const responses = await Promise.all(
        ids.map((id) => search({ id, size: 1 })),
      );
      if (token !== loadToken) return;

      const seen = new Set<string>();
      const items: SearchItem[] = [];
      for (const response of responses) {
        for (const hit of response.items) {
          if (hit.id === recordId || seen.has(hit.id)) continue;
          seen.add(hit.id);
          items.push(hit);
        }
      }
      related = items;
    } catch (err) {
      if (token !== loadToken) return;
      error = err instanceof Error ? err.message : "Failed to load related records.";
    } finally {
      if (token === loadToken) {
        loading = false;
      }
    }
  }

  function handleDialogClose() {
    onClose();
  }
</script>

<dialog class="related-records-dialog" bind:this={dialogEl} onclose={handleDialogClose}>
  <div class="related-records-panel">
    <header class="related-records-header">
      <h2>Related records</h2>
      <button
        type="button"
        class="related-records-close"
        aria-label="Close related records"
        onclick={() => dialogEl?.close()}
      >
        ×
      </button>
    </header>

    {#if !loading && !error && related.length > 0}
      <RelatedRecordsGraph source={item} {related} />
    {/if}

    <p class="related-records-source">
      From <strong>{item.title}</strong>
    </p>

    {#if loading}
      <p class="related-records-status">Looking up linked @id values…</p>
    {:else if error}
      <p class="related-records-status error">{error}</p>
    {:else if related.length === 0}
      <p class="related-records-status">
        {#if scannedIds === 0}
          No @id references found in this record’s JSON-LD.
        {:else}
          Checked {scannedIds} linked @id{scannedIds === 1 ? "" : "s"}; none matched
          records in the index.
        {/if}
      </p>
    {:else}
      <p class="related-records-status">
        Found {related.length} of {scannedIds} linked @id{scannedIds === 1 ? "" : "s"} in
        the index.
      </p>
      <div class="related-records-results">
        {#each related as hit (hit.id)}
          <ResultCard item={hit} showRelatedLink={false} />
        {/each}
      </div>
    {/if}
  </div>
</dialog>
