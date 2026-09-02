<script lang="ts">
  const STORAGE_KEY = "odis-dev-banner-dismissed";

  let visible = $state(
    typeof localStorage === "undefined" || localStorage.getItem(STORAGE_KEY) !== "1",
  );

  function dismiss() {
    visible = false;
    localStorage.setItem(STORAGE_KEY, "1");
  }
</script>

{#if visible}
  <div class="dev-banner" role="note">
    <p>
      ODIS Search is under active development, so features and data may change without notice.
      Found a bug or have a suggestion?
      <a href="https://github.com/iodepo/odis-ui/issues" target="_blank" rel="noopener noreferrer">
        Open an issue on GitHub
      </a>.
    </p>
    <button type="button" class="dev-banner-close" aria-label="Dismiss banner" onclick={dismiss}>
      ×
    </button>
  </div>
{/if}
