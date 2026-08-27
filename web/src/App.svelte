<script lang="ts">
  import { onMount } from "svelte";
  import FacetPanel from "./lib/FacetPanel.svelte";
  import DevBanner from "./lib/DevBanner.svelte";
  import SearchSettings from "./lib/SearchSettings.svelte";
  import SpatialExtentMap from "./lib/SpatialExtentMap.svelte";
  import TypeBadge from "./lib/TypeBadge.svelte";
  import TypePillBar from "./lib/TypePillBar.svelte";
  import SummaryText from "./lib/SummaryText.svelte";
  import ActiveFilters from "./lib/ActiveFilters.svelte";
  import {
    recordUrl,
    search,
    type SearchFacets,
    type SearchParams,
    type SearchResponse,
  } from "./lib/api";
  import { formatNumber } from "./lib/format";
  import { buildSearchUrl, parseSearchParams, toggleValue } from "./lib/url";
  import {
    readGraphFragmentsPreference,
    writeGraphFragmentsPreference,
  } from "./lib/searchSettings";
  import "./app.css";

  let query = $state("");
  let selectedTypes = $state<string[]>([]);
  let selectedSources = $state<string[]>([]);
  let page = $state(1);
  let results: SearchResponse | null = $state(null);
  let searchError: string | null = $state(null);
  let loading = $state(false);
  let loadingMore = $state(false);
  let scrollSentinel: HTMLDivElement | undefined = $state();
  let scrollObserver: IntersectionObserver | undefined = $state();
  let typeOptions = $state<string[]>([]);
  let sourceOptions = $state<{ id: string; name?: string | null }[]>([]);
  let includeGraphFragments = $state(readGraphFragmentsPreference());
  let settingsOpen = $state(false);

  const hasMore = $derived(results !== null && results.items.length < results.total);

  function updateTypeOptions(facets: SearchFacets) {
    typeOptions = facets.types.map((bucket) => bucket.value);
  }

  function updateSourceOptions(facets: SearchFacets) {
    const byId = new Map(sourceOptions.map((option) => [option.id, option]));
    for (const bucket of facets.sources) {
      const existing = byId.get(bucket.id);
      byId.set(bucket.id, {
        id: bucket.id,
        name: bucket.name ?? existing?.name,
      });
    }
    const order = facets.sources.map((bucket) => bucket.id);
    const known = [...byId.keys()].filter((id) => !order.includes(id));
    sourceOptions = [...order, ...known].map((id) => byId.get(id)!);
  }

  function currentParams(): SearchParams {
    const params: SearchParams = {
      q: query || undefined,
      types: selectedTypes.length ? selectedTypes : undefined,
      source: selectedSources.length ? selectedSources : undefined,
      page,
    };
    if (includeGraphFragments) {
      params.include_graph_fragments = true;
    }
    return params;
  }

  async function runSearch(pushUrl = true, append = false) {
    if (append) {
      if (loading || !hasMore) return;
      loadingMore = true;
    } else {
      if (loading) return;
      loading = true;
      searchError = null;
    }

    const params = currentParams();

    if (pushUrl && !append) {
      history.replaceState(null, "", buildSearchUrl(params));
    }

    try {
      const response = await search(params);
      if (append && results) {
        results = {
          ...response,
          items: [...results.items, ...response.items],
        };
      } else {
        results = response;
      }
      updateTypeOptions(response.facets);
      updateSourceOptions(response.facets);
    } catch (e) {
      if (append) {
        page = Math.max(1, page - 1);
      } else {
        searchError = e instanceof Error ? e.message : "Search failed";
        results = null;
      }
    } finally {
      loading = false;
      loadingMore = false;
    }
  }

  async function loadMore() {
    if (!hasMore || loading || loadingMore || searchError) return;
    page += 1;
    await runSearch(false, true);
  }

  function applyFromUrl(url: URL) {
    const params = parseSearchParams(url);
    query = params.q ?? "";
    selectedTypes = params.types ?? [];
    selectedSources = params.source ?? [];
    page = params.page ?? 1;
    if (url.searchParams.has("include_graph_fragments")) {
      includeGraphFragments = Boolean(params.include_graph_fragments);
      writeGraphFragmentsPreference(includeGraphFragments);
    }
  }

  onMount(() => {
    applyFromUrl(new URL(window.location.href));
    page = 1;

    scrollObserver = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          void loadMore();
        }
      },
      { rootMargin: "240px" },
    );

    void runSearch(false);

    const onPopState = () => {
      applyFromUrl(new URL(window.location.href));
      page = 1;
      void runSearch(false);
    };
    window.addEventListener("popstate", onPopState);
    return () => {
      window.removeEventListener("popstate", onPopState);
      scrollObserver?.disconnect();
      scrollObserver = undefined;
    };
  });

  $effect(() => {
    const node = scrollSentinel;
    const observer = scrollObserver;
    if (!node || !observer) return;
    observer.observe(node);
    return () => observer.unobserve(node);
  });

  async function handleSearch(event: Event) {
    event.preventDefault();
    page = 1;
    await runSearch();
  }

  async function handleSearchBoxSearch(event: Event) {
    // Native search clear (×) fires a search event with an empty value.
    const target = event.currentTarget as HTMLInputElement;
    if (target.value !== "") return;
    query = "";
    page = 1;
    await runSearch();
  }

  async function handleTypeToggle(value: string) {
    selectedTypes = toggleValue(selectedTypes, value);
    page = 1;
    await runSearch();
  }

  async function handleAllTypes() {
    selectedTypes = [];
    page = 1;
    await runSearch();
  }

  async function handleSourceToggle(id: string) {
    selectedSources = toggleValue(selectedSources, id);
    page = 1;
    await runSearch();
  }

  async function handleClearFilters() {
    selectedTypes = [];
    selectedSources = [];
    page = 1;
    await runSearch();
  }

  async function handleGraphFragmentsChange(enabled: boolean) {
    includeGraphFragments = enabled;
    writeGraphFragmentsPreference(enabled);
    selectedTypes = [];
    typeOptions = [];
    page = 1;
    await runSearch();
  }

  async function handleHomeClick(event: MouseEvent) {
    event.preventDefault();
    query = "";
    selectedTypes = [];
    selectedSources = [];
    sourceOptions = [];
    page = 1;
    await runSearch();
  }
</script>

<DevBanner />

<main>
  <header class="page-header">
    <div class="page-header-top">
      <div class="page-header-brand">
        <img
          class="site-logo"
          src="/iode-unesco-logo-1024x449.png"
          width="1024"
          height="449"
          alt="UNESCO IOC / International Oceanographic Data and Information Exchange (IODE)"
        />
        <h1>
          <a href="/" class="site-title" onclick={handleHomeClick}>
            <img
              class="odis-logo"
              src="/ODIS_logo_cropped.png"
              width="940"
              height="390"
              alt="ODIS"
            />
            Search
          </a>
        </h1>
      </div>
      <div class="page-header-actions">
        <a
          href="#settings"
          class="github-link"
          aria-label="Search settings"
          title="Search settings"
          onclick={(event) => {
            event.preventDefault();
            settingsOpen = true;
          }}
        >
          <svg
            class="settings-icon"
            viewBox="0 0 64 64"
            width="20"
            height="20"
            xmlns="http://www.w3.org/2000/svg"
            stroke-width="3"
            stroke="currentColor"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M45,14.67l-2.76,2a1,1,0,0,1-1,.11L37.65,15.3a1,1,0,0,1-.61-.76l-.66-3.77a1,1,0,0,0-1-.84H30.52a1,1,0,0,0-1,.77l-.93,3.72a1,1,0,0,1-.53.65l-3.3,1.66a1,1,0,0,1-1-.08l-3-2.13a1,1,0,0,0-1.31.12l-3.65,3.74a1,1,0,0,0-.13,1.26l1.87,2.88a1,1,0,0,1,.1.89L16.34,27a1,1,0,0,1-.68.63l-3.85,1.06a1,1,0,0,0-.74,1v4.74a1,1,0,0,0,.8,1l3.9.8a1,1,0,0,1,.72.57l1.42,3.15a1,1,0,0,1-.05.92l-2.13,3.63a1,1,0,0,0,.17,1.24L19.32,49a1,1,0,0,0,1.29.09L23.49,47a1,1,0,0,1,1-.1l3.74,1.67a1,1,0,0,1,.59.75l.66,3.79a1,1,0,0,0,1,.84h4.89a1,1,0,0,0,1-.86l.58-4a1,1,0,0,1,.58-.77l3.58-1.62a1,1,0,0,1,1,.09l3.14,2.12a1,1,0,0,0,1.3-.15L50,45.06a1,1,0,0,0,.09-1.27l-2.08-3a1,1,0,0,1-.09-1l1.48-3.43a1,1,0,0,1,.71-.59L53.77,35a1,1,0,0,0,.8-1V29.42a1,1,0,0,0-.8-1l-3.72-.78a1,1,0,0,1-.73-.62l-1.45-3.65a1,1,0,0,1,.11-.94l2.15-3.14A1,1,0,0,0,50,18l-3.71-3.25A1,1,0,0,0,45,14.67Z"
            />
            <circle cx="32.82" cy="31.94" r="9.94" />
          </svg>
        </a>
        <a
          href="https://github.com/iobis/odis-ui"
          class="github-link"
          aria-label="View source on GitHub"
          target="_blank"
          rel="noopener noreferrer"
        >
          <svg viewBox="0 0 16 16" width="20" height="20" aria-hidden="true">
            <path
              fill="currentColor"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
        </a>
      </div>
    </div>
    <p class="subtitle">Faceted search over ODIS metadata records</p>
  </header>

  <form class="search-form" onsubmit={handleSearch}>
    <input
      type="search"
      bind:value={query}
      placeholder="Search title, description, keywords…"
      onsearch={handleSearchBoxSearch}
    />
    <button type="submit" disabled={loading}>{loading ? "Searching…" : "Search"}</button>
  </form>

  <TypePillBar
    {typeOptions}
    {selectedTypes}
    onAllTypes={handleAllTypes}
    onTypeToggle={handleTypeToggle}
  />

  <ActiveFilters
    {selectedTypes}
    {selectedSources}
    {sourceOptions}
    onTypeToggle={handleTypeToggle}
    onSourceToggle={handleSourceToggle}
    onClearAll={handleClearFilters}
  />

  <div class="layout">
    <FacetPanel
      facets={results?.facets ?? null}
      {typeOptions}
      {sourceOptions}
      {selectedTypes}
      {selectedSources}
      onTypeToggle={handleTypeToggle}
      onSourceToggle={handleSourceToggle}
    />

    <section class="results">
      {#if searchError}
        <p class="error">{searchError}</p>
      {/if}

      {#if results}
        <p class="results-meta">{formatNumber(results.total)} result{results.total === 1 ? "" : "s"}</p>
        {#each results.items as item (item.id)}
          <article class="result-card">
            <TypeBadge type={item.type} />
            <h2>
              {#if item.url}
                <a href={item.url} class="result-title-link" target="_blank" rel="noopener noreferrer"
                  >{item.title}</a
                >
              {:else}
                {item.title}
              {/if}
            </h2>
            {#if item.source?.name}
              <p class="source">{item.source.name}</p>
            {/if}
            {#if item.url}
              <p class="record-url">
                <a href={item.url} target="_blank" rel="noopener noreferrer">{item.url}</a>
              </p>
            {/if}
            {#if item.summary}
              <SummaryText summary={item.summary} />
            {/if}
            {#if item.spatial && (item.spatial.boxes.length || item.spatial.points.length)}
              <div class="card-foot">
                <SpatialExtentMap spatial={item.spatial} recordType={item.type} />
              </div>
            {/if}
            <div class="record-links">
              <a class="record-link" href={recordUrl(item.id)} target="_blank" rel="noopener noreferrer">
                API record
              </a>
              {#if item.elasticsearch_document_url}
                <a
                  class="record-link"
                  href={item.elasticsearch_document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Elasticsearch document
                </a>
              {/if}
            </div>
          </article>
        {/each}

        {#if hasMore}
          <div class="scroll-sentinel" bind:this={scrollSentinel} aria-hidden="true"></div>
        {/if}

        {#if loadingMore}
          <p class="results-meta loading-more">Loading more…</p>
        {:else if !hasMore && results.items.length > 0}
          <p class="results-meta end-of-results">End of results</p>
        {/if}
      {:else if loading}
        <p class="results-meta">Searching…</p>
      {/if}
    </section>
  </div>
</main>

<SearchSettings
  open={settingsOpen}
  {includeGraphFragments}
  onClose={() => (settingsOpen = false)}
  onGraphFragmentsChange={handleGraphFragmentsChange}
/>
