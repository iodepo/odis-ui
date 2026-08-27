<script lang="ts">
  type Props = {
    open: boolean;
    includeGraphFragments: boolean;
    onClose: () => void;
    onGraphFragmentsChange: (enabled: boolean) => void;
  };

  let {
    open,
    includeGraphFragments,
    onClose,
    onGraphFragmentsChange,
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

    <label class="search-settings-option">
      <input
        type="checkbox"
        checked={includeGraphFragments}
        onchange={(event) => onGraphFragmentsChange((event.currentTarget as HTMLInputElement).checked)}
      />
      <span>
        <strong>Include graph fragments</strong>
        <span class="search-settings-hint">
          Show structural JSON-LD nodes (e.g. DataDownload, Place, GeoShape). Many hits have no
          title and are intended for harvest debugging.
        </span>
      </span>
    </label>
  </form>
</dialog>
