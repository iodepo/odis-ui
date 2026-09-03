<script lang="ts">
  import HighlightText from "./HighlightText.svelte";
  import SpatialExtentMap from "./SpatialExtentMap.svelte";
  import SummaryText from "./SummaryText.svelte";
  import TypeBadge from "./TypeBadge.svelte";
  import { recordUrl, type SearchItem } from "./api";
  import { resolveTypeTheme } from "./typeTheme";

  interface Props {
    item: SearchItem;
  }

  let { item }: Props = $props();

  const theme = $derived(resolveTypeTheme(item.type));
  const facts = $derived(item.facts ?? []);
  const highlightedTitle = $derived(item.highlight?.title ?? null);
  const highlightedSummary = $derived(item.highlight?.summary ?? null);

  let popoverEl: HTMLSpanElement | null = $state(null);
  let rafId: number | null = null;

  function updatePopoverPosition(e: PointerEvent) {
    const x = e.clientX + 12;
    const y = e.clientY + 12;

    if (rafId !== null) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      if (!popoverEl) return;
      const pad = 8;
      const left = Math.min(x, innerWidth - popoverEl.offsetWidth - pad);
      const top = Math.min(y, innerHeight - popoverEl.offsetHeight - pad);
      popoverEl.style.left = `${Math.max(pad, left)}px`;
      popoverEl.style.top = `${Math.max(pad, top)}px`;
    });
  }

  function formatLastIndexed(value: string): string {
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }
</script>

<article class="result-card {theme.badge}">
  <TypeBadge type={item.type} />
  <h2>
    {#if item.url}
      <a href={item.url} class="result-title-link" target="_blank" rel="noopener noreferrer">
        {#if highlightedTitle}
          <HighlightText text={highlightedTitle} />
        {:else}
          {item.title}
        {/if}
      </a>
    {:else if highlightedTitle}
      <HighlightText text={highlightedTitle} />
    {:else}
      {item.title}
    {/if}
  </h2>
  {#if item.source?.name}
    <p class="source-meta">
      <span
        class="source-pill-wrap"
        onpointerenter={(e) => {
          updatePopoverPosition(e);
        }}
        onpointermove={(e) => {
          updatePopoverPosition(e);
        }}
      >
        <span class="source-pill">{item.source.name}</span>

        <span
          class="source-popover"
          role="tooltip"
          bind:this={popoverEl}
        >
          <strong>{item.source.name}</strong>
          {#if item.source.domain}
            <span class="pop-row"
              ><span class="pop-label">Domain</span>
              <span class="pop-value">{item.source.domain}</span></span
            >
          {/if}
          {#if item.source.url}
            <span class="pop-row"
              ><span class="pop-label">URL</span>
              <span class="pop-value"
                >{item.source.url}</span
              ></span
            >
          {/if}
          {#if item.source.last_indexed != null}
            <span class="pop-row"
              ><span class="pop-label">Last indexed</span>
              <span class="pop-value"
                >{formatLastIndexed(item.source.last_indexed)}</span
              ></span
            >
          {/if}
        </span>
      </span>
    </p>
  {/if}
  {#if facts.length}
    <dl class="facts">
      {#each facts as fact (fact.label + fact.value)}
        <div>
          <dt>{fact.label}</dt>
          <dd>
            {#if fact.href}
              <a href={fact.href} target="_blank" rel="noopener noreferrer">{fact.value}</a>
            {:else}
              {fact.value}
            {/if}
          </dd>
        </div>
      {/each}
    </dl>
  {/if}
  {#if highlightedSummary || item.summary}
    <SummaryText summary={item.summary ?? ""} highlightedSummary={highlightedSummary} />
  {/if}
  {#if item.spatial && (item.spatial.boxes.length || item.spatial.points.length)}
    <div class="card-foot">
      <SpatialExtentMap spatial={item.spatial} recordType={item.type} />
    </div>
  {/if}
  <div class="record-links">
    {#if item.url}
      <a class="record-link" href={item.url} target="_blank" rel="noopener noreferrer">URL</a>
    {/if}
    <a class="record-link" href={recordUrl(item.id)} target="_blank" rel="noopener noreferrer">
      API record
    </a>
    {#if item.elasticsearch_document_url}
      <a
        class="record-link"
        href={item.elasticsearch_document_url}
        target="_blank" rel="noopener noreferrer"
      >
        Elasticsearch document
      </a>
    {/if}
  </div>
</article>
