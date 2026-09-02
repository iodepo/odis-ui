<script lang="ts">
  import { parseEmHighlight, type HighlightSegment } from "./highlight";

  type Props = {
    text?: string;
    segments?: HighlightSegment[];
  };

  let { text = "", segments }: Props = $props();

  const resolvedSegments = $derived(segments ?? parseEmHighlight(text));
</script>

{#each resolvedSegments as segment, index (`${index}:${segment.match}:${segment.text}`)}
  {#if segment.match}
    <mark class="search-hit">{segment.text}</mark>
  {:else}
    {segment.text}
  {/if}
{/each}
