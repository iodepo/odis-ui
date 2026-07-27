<script lang="ts">
  type Props = {
    open: boolean;
    includeGraphFragments: boolean;
    disabled?: boolean;
    onClose: () => void;
    onGraphFragmentsChange: (enabled: boolean) => void;
  };

  let {
    open,
    includeGraphFragments,
    disabled = false,
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

    <p class="search-settings-note">Applies to the ODIS backend only.</p>

    <label class="search-settings-option">
      <input
        type="checkbox"
        checked={includeGraphFragments}
        {disabled}
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
