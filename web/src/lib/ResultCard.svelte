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
      <span class="source-pill" title="Data source">{item.source.name}</span>
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
