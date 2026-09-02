<script lang="ts">
  import HighlightText from "./HighlightText.svelte";
  import { parseEmHighlight, truncateHighlightSegments } from "./highlight";
  import { prepareSummary } from "./summary";

  type Props = {
    summary: string;
    highlightedSummary?: string | null;
    collapsedLength?: number;
  };

  let { summary, highlightedSummary = null, collapsedLength = 560 }: Props = $props();

  let expanded = $state(false);

  $effect(() => {
    summary;
    highlightedSummary;
    expanded = false;
  });

  const prepared = $derived(prepareSummary(summary));
  const highlightSegments = $derived(
    highlightedSummary ? parseEmHighlight(highlightedSummary) : [],
  );
  const plainLength = $derived(
    highlightedSummary
      ? highlightSegments.map((segment) => segment.text).join("").length
      : prepared.text.length,
  );
  const collapsible = $derived(plainLength > collapsedLength);
  const displayText = $derived(
    !collapsible || expanded ? prepared.text : `${prepared.text.slice(0, collapsedLength).trimEnd()}…`,
  );
  const displaySegments = $derived(
    !collapsible || expanded
      ? highlightSegments
      : truncateHighlightSegments(highlightSegments, collapsedLength),
  );
  const showHighlightEllipsis = $derived(collapsible && !expanded && highlightedSummary);
</script>

<p class:summary-structured={prepared.structured}>
  {#if highlightedSummary}
    <HighlightText segments={displaySegments} />
    {#if showHighlightEllipsis}…{/if}
  {:else}
    {displayText}
  {/if}
  {#if collapsible}
    <button type="button" class="summary-toggle" onclick={() => (expanded = !expanded)}>
      {expanded ? "Show less" : "Show more"}
    </button>
  {/if}
</p>
