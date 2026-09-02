<script lang="ts">
  import type { SearchFacets } from "./api";
  import { formatCompactNumber } from "./format";
  import { formatTypeLabel } from "./labels";

  interface Props {
    typeOptions: string[];
    selectedTypes: string[];
    facets: SearchFacets | null;
    total: number | null;
    onAllTypes: () => void;
    onTypeToggle: (value: string) => void;
  }

  let { typeOptions, selectedTypes, facets, total, onAllTypes, onTypeToggle }: Props = $props();

  const allTypesActive = $derived(selectedTypes.length === 0);

  function typeCount(value: string): number | null {
    const bucket = facets?.types.find((item) => item.value === value);
    return bucket ? bucket.count : null;
  }
</script>

<div class="type-pillbar" role="group" aria-label="Record type filters">
  <button type="button" class="pill" class:on={allTypesActive} onclick={onAllTypes}>
    All types
    {#if total != null}
      <span class="cnt">{formatCompactNumber(total)}</span>
    {/if}
  </button>

  {#each typeOptions as value (value)}
    {@const count = typeCount(value)}
    <button
      type="button"
      class="pill"
      class:on={selectedTypes.includes(value)}
      onclick={() => onTypeToggle(value)}
    >
      {formatTypeLabel(value)}
      {#if count != null}
        <span class="cnt">{formatCompactNumber(count)}</span>
      {/if}
    </button>
  {/each}
</div>

<style>
  .type-pillbar {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
    margin: 0.85rem 0 0;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.32rem 0.8rem;
    border-radius: 999px;
    border: 1px solid var(--line);
    background: var(--paper-raised);
    color: var(--ink-soft);
    font-size: 0.78rem;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
    line-height: 1.2;
  }

  .pill .cnt {
    font-size: 0.68rem;
    font-variant-numeric: tabular-nums;
    opacity: 0.7;
  }

  .pill:hover {
    color: var(--ink);
    border-color: var(--ink-faint);
  }

  .pill.on {
    background: var(--ink);
    border-color: var(--ink);
    color: var(--paper-raised);
  }

  .pill.on:hover {
    color: var(--paper-raised);
  }

  .pill.on .cnt {
    opacity: 0.65;
  }
</style>
