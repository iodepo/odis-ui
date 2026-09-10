<script lang="ts">
  type Props = {
    open: boolean;
    includeGraphFragments: boolean;
    showRelatedRecords: boolean;
    onClose: () => void;
    onGraphFragmentsChange: (enabled: boolean) => void;
    onRelatedRecordsChange: (enabled: boolean) => void;
  };

  let {
    open,
    includeGraphFragments,
    showRelatedRecords,
    onClose,
    onGraphFragmentsChange,
    onRelatedRecordsChange,
  }: Props = $props();

  let dialogEl: HTMLDialogElement | undefined = $state();

  $effect(() => {
    const dialog = dialogEl;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  });

  function handleDialogClose() {
    onClose();
  }
</script>

<dialog class="search-settings-dialog" bind:this={dialogEl} onclose={handleDialogClose}>
  <form method="dialog" class="search-settings-panel">
    <header class="search-settings-header">
      <h2>Search settings</h2>
      <button type="submit" class="search-settings-close" aria-label="Close settings">×</button>
    </header>

    <div class="search-settings-options">
      <label class="search-settings-option">
        <input
          type="checkbox"
          checked={includeGraphFragments}
          onchange={(event) =>
            onGraphFragmentsChange((event.currentTarget as HTMLInputElement).checked)}
        />
        <span>
          <strong>Include graph fragments</strong>
          <span class="search-settings-hint">
            Show structural JSON-LD nodes (e.g. DataDownload, Place, GeoShape). Many hits have no
            title and are intended for harvest debugging.
          </span>
        </span>
      </label>

      <label class="search-settings-option">
        <input
          type="checkbox"
          checked={showRelatedRecords}
          onchange={(event) =>
            onRelatedRecordsChange((event.currentTarget as HTMLInputElement).checked)}
        />
        <span>
          <strong>Show related records</strong>
          <span class="search-settings-hint">
            Add a “Related records” link on each result that looks up linked @id values in the
            index.
          </span>
        </span>
      </label>
    </div>
  </form>
</dialog>
