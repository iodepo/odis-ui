<script lang="ts">
  import { onMount } from "svelte";
  import FacetPanel from "./lib/FacetPanel.svelte";
  import DevBanner from "./lib/DevBanner.svelte";
  import NetworkStatus from "./lib/NetworkStatus.svelte";
  import SearchSettings from "./lib/SearchSettings.svelte";
  import ResultCard from "./lib/ResultCard.svelte";
  import TypePillBar from "./lib/TypePillBar.svelte";
  import {
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
  import { trackSearch } from "./lib/analytics";
  import "./app.css";

  type AppView = "search" | "network";

  function viewFromPath(pathname: string): AppView {
    return pathname === "/network" || pathname === "/network/" ? "network" : "search";
  }

  let view = $state<AppView>(viewFromPath(window.location.pathname));
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
  let searchGeneration = 0;

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
    const params = currentParams();

    if (append) {
      if (loadingMore || !hasMore) return;
      const generation = searchGeneration;
      loadingMore = true;

      try {
        const response = await search(params);
        if (generation !== searchGeneration) return;
        if (results) {
          results = {
            ...response,
            items: [...results.items, ...response.items],
          };
        }
      } catch (e) {
        if (generation !== searchGeneration) return;
        page = Math.max(1, page - 1);
      } finally {
        if (generation === searchGeneration) {
          loadingMore = false;
        }
      }
      return;
    }

    searchGeneration += 1;
    const generation = searchGeneration;
    loading = true;
    loadingMore = false;
    searchError = null;

    if (pushUrl) {
      history.replaceState(null, "", buildSearchUrl(params));
    }

    try {
      const response = await search(params);
      if (generation !== searchGeneration) return;
      results = response;
      updateTypeOptions(response.facets);
      updateSourceOptions(response.facets);
      if (params.q) {
        trackSearch({
          search_term: params.q,
          result_count: response.total,
          types: params.types,
          sources: params.source,
        });
      }
    } catch (e) {
      if (generation !== searchGeneration) return;
      searchError = e instanceof Error ? e.message : "Search failed";
      results = null;
    } finally {
      if (generation === searchGeneration) {
        loading = false;
      }
    }
  }

  async function loadMore() {
    if (!hasMore || loading || loadingMore || searchError) return;
    page += 1;
    await runSearch(false, true);
  }

  function applyFromUrl(url: URL) {
    view = viewFromPath(url.pathname);
    if (view !== "search") return;
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

    if (view === "search") {
      void runSearch(false);
    }

    const onPopState = () => {
      applyFromUrl(new URL(window.location.href));
      if (view === "search") {
        page = 1;
        void runSearch(false);
      }
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
    view = "search";
    query = "";
    selectedTypes = [];
    selectedSources = [];
    sourceOptions = [];
    page = 1;
    await runSearch();
  }

  function handleNetworkClick(event: MouseEvent) {
    event.preventDefault();
    if (view === "network") return;
    view = "network";
    history.pushState(null, "", "/network");
  }
</script>

<DevBanner />

<header class="brandbar">
  <div class="brandbar-inner">
    <div class="page-header-brand">
      <a href="/" class="site-title" onclick={handleHomeClick}>
        <img
          class="site-logo"
          src="/ioc-logo.svg"
          width="1920"
          height="1405"
          alt="Intergovernmental Oceanographic Commission (IOC) of UNESCO"
        />
        <span class="brand-divider" aria-hidden="true"></span>
        <span class="sitename">ODIS Search</span>
      </a>
    </div>
    <div class="page-header-actions">
      <a
        href="/network"
        class="nav-text-link"
        class:active={view === "network"}
        onclick={handleNetworkClick}
      >
        Network status
      </a>
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
</header>

{#if view === "network"}
  <main class="page network-view">
    <NetworkStatus />
  </main>
{:else}
  <div class="hero-search">
    <div class="hero-search-inner">
      <h1>Search ocean data and information</h1>
      <form class="search-form" onsubmit={handleSearch}>
        <span class="search-glyph" aria-hidden="true">
          <svg viewBox="0 0 24 24" width="20" height="20">
            <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
            <path
              d="M16.5 16.5 21 21"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </span>
        <input
          type="search"
          bind:value={query}
          placeholder="Search title, description, keywords…"
          onsearch={handleSearchBoxSearch}
          aria-label="Search"
        />
      </form>

      <TypePillBar
        {typeOptions}
        {selectedTypes}
        facets={results?.facets ?? null}
        total={results?.total ?? null}
        onAllTypes={handleAllTypes}
        onTypeToggle={handleTypeToggle}
      />
    </div>
  </div>

  <main class="page">
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
            <ResultCard {item} />
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
{/if}

<SearchSettings
  open={settingsOpen}
  {includeGraphFragments}
  onClose={() => (settingsOpen = false)}
  onGraphFragmentsChange={handleGraphFragmentsChange}
/>
