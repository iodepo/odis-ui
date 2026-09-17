<script lang="ts">
  import type { Map as MapLibreMap } from "maplibre-gl";
  import type { SpatialExtent } from "./api";
  import { resolveTypeTheme } from "./typeTheme";
  import {
    OBIS_COASTLINE_STYLE,
    boundsToSvg,
    extentThemeClass,
    extentThemeColors,
    formatExtentLabel,
    spatialToGeoJSON,
    unionBounds,
  } from "./spatial";

  interface Props {
    spatial: SpatialExtent;
    recordType: string;
  }

  let { spatial, recordType }: Props = $props();

  const bounds = $derived(unionBounds(spatial));
  const svg = $derived(bounds ? boundsToSvg(bounds) : null);
  const label = $derived(bounds ? formatExtentLabel(bounds) : "");
  const themeKey = $derived(resolveTypeTheme(recordType).key);
  const themeClass = $derived(extentThemeClass[themeKey]);
  const colors = $derived(extentThemeColors[themeKey]);

  let expanded = $state(false);
  let mapEl: HTMLDivElement | null = $state(null);
  let mapLoading = $state(false);
  let mapError = $state(false);

  function toggleExpanded() {
    expanded = !expanded;
  }

  $effect(() => {
    if (!expanded) {
      mapLoading = false;
      mapError = false;
      return;
    }
    const container = mapEl;
    if (!container || !bounds) return;

    const geojson = spatialToGeoJSON(spatial);
    const { stroke, fill } = colors;
    const extentSpatial = spatial;

    let cancelled = false;
    let map: MapLibreMap | null = null;
    let onResize: (() => void) | null = null;

    mapLoading = true;
    mapError = false;

    (async () => {
      const [maplibre, workerMod] = await Promise.all([
        import("maplibre-gl"),
        import("maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url"),
        import("maplibre-gl/dist/maplibre-gl.css"),
      ]);
      if (cancelled) return;

      const { Map, NavigationControl, LngLatBounds, setWorkerUrl } = maplibre;
      setWorkerUrl(workerMod.default);

      map = new Map({
        container,
        style: OBIS_COASTLINE_STYLE,
        center: [0, 20],
        zoom: 1,
        projection: "mercator",
        attributionControl: false,
        cooperativeGestures: true,
      });

      map.addControl(new NavigationControl({ showCompass: false }), "top-right");

      const fitToExtent = () => {
        if (!map) return;
        const lngLatBounds = new LngLatBounds();
        for (const box of extentSpatial.boxes) {
          lngLatBounds.extend([box.west, box.south]);
          lngLatBounds.extend([box.east, box.north]);
        }
        for (const point of extentSpatial.points) {
          lngLatBounds.extend([point.lon, point.lat]);
        }
        if (!lngLatBounds.isEmpty()) {
          map.fitBounds(lngLatBounds, {
            padding: 36,
            maxZoom: 5,
            duration: 0,
          });
        }
      };

      map.on("load", () => {
        if (!map || cancelled) return;

        map.addSource("extent", {
          type: "geojson",
          data: geojson,
        });

        map.addLayer({
          id: "extent-fill",
          type: "fill",
          source: "extent",
          filter: ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
          paint: {
            "fill-color": fill,
            "fill-opacity": 0.55,
          },
        });

        map.addLayer({
          id: "extent-line",
          type: "line",
          source: "extent",
          filter: ["in", ["geometry-type"], ["literal", ["Polygon", "MultiPolygon"]]],
          paint: {
            "line-color": stroke,
            "line-width": 1.5,
          },
        });

        map.addLayer({
          id: "extent-points",
          type: "circle",
          source: "extent",
          filter: ["==", ["geometry-type"], "Point"],
          paint: {
            "circle-radius": 6,
            "circle-color": fill,
            "circle-stroke-color": stroke,
            "circle-stroke-width": 2,
          },
        });

        mapLoading = false;
        requestAnimationFrame(() => {
          map?.resize();
          fitToExtent();
        });
      });

      map.on("error", () => {
        // Keep the map chrome visible; tile errors shouldn't blank the UI.
      });

      onResize = () => map?.resize();
      window.addEventListener("resize", onResize);
    })().catch(() => {
      if (!cancelled) {
        mapLoading = false;
        mapError = true;
      }
    });

    return () => {
      cancelled = true;
      if (onResize) window.removeEventListener("resize", onResize);
      map?.remove();
      map = null;
    };
  });
</script>

{#if bounds && svg}
  <div class="extent-root">
    <button
      type="button"
      class="extent"
      aria-expanded={expanded}
      aria-controls={expanded ? "extent-map-panel" : undefined}
      aria-label="{expanded ? 'Hide' : 'Show'} map for spatial extent {label}"
      onclick={toggleExpanded}
    >
      <svg viewBox="0 0 36 20" width="26" height="15" aria-hidden="true">
        <rect
          x="0.5"
          y="0.5"
          width="35"
          height="19"
          fill="none"
          stroke="var(--line-strong)"
        />
        {#if svg.isPoint}
          <circle
            class="extent-marker {themeClass}"
            cx={svg.x}
            cy={svg.y}
            r="1.4"
          />
        {:else}
          <rect
            class="extent-marker {themeClass}"
            x={svg.x}
            y={svg.y}
            width={svg.width}
            height={svg.height}
            stroke-width="0.75"
          />
        {/if}
      </svg>
      <span class="extent-label">{label}</span>
    </button>

    {#if expanded}
      <div id="extent-map-panel" class="extent-map-panel" role="region" aria-label="Spatial extent map">
        <div class="extent-map-frame">
          {#if mapLoading}
            <p class="extent-map-status">Loading map…</p>
          {:else if mapError}
            <p class="extent-map-status">Could not load map.</p>
          {/if}
          <div class="extent-map" bind:this={mapEl}></div>
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .extent-root {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.65rem;
    width: 100%;
  }

  .extent {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    margin: 0;
    padding: 0;
    border: 0;
    background: none;
    color: var(--ink-soft);
    font: inherit;
    font-size: 0.72rem;
    cursor: pointer;
    border-radius: 3px;
  }

  .extent:hover {
    color: var(--ink);
  }

  .extent:focus-visible {
    outline: 2px solid var(--depth);
    outline-offset: 2px;
  }

  .extent svg {
    flex: none;
  }

  .extent-label {
    font-variant-numeric: tabular-nums;
    line-height: 1.3;
    text-decoration: underline;
    text-decoration-color: transparent;
    text-underline-offset: 2px;
  }

  .extent:hover .extent-label {
    text-decoration-color: currentColor;
  }

  .extent-map-panel {
    width: 100%;
  }

  .extent-map-frame {
    position: relative;
    width: 100%;
    height: 14rem;
    border: 1px solid var(--line);
    border-radius: 6px;
    overflow: hidden;
    background: #fff;
  }

  .extent-map {
    width: 100%;
    height: 100%;
  }

  .extent-map-status {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0;
    font-size: 0.8rem;
    color: var(--ink-faint);
    pointer-events: none;
    background: #fff;
  }

  .extent-map :global(.maplibregl-canvas) {
    outline: none;
  }

  .extent-map :global(.maplibregl-ctrl-group) {
    border: 1px solid var(--line) !important;
    box-shadow: none !important;
    border-radius: 4px !important;
    overflow: hidden;
  }

  .extent-map :global(.maplibregl-ctrl-group button) {
    width: 28px !important;
    height: 28px !important;
  }

  .extent-marker.dataset {
    fill: var(--dataset-tint);
    stroke: var(--dataset);
  }

  .extent-marker.literature {
    fill: var(--literature-tint);
    stroke: var(--literature);
  }

  .extent-marker.org {
    fill: var(--org-tint);
    stroke: var(--org);
  }

  .extent-marker.training {
    fill: var(--training-tint);
    stroke: var(--training);
  }

  .extent-marker.project {
    fill: var(--project-tint);
    stroke: var(--project);
  }

  .extent-marker.default {
    fill: var(--depth-tint);
    stroke: var(--depth);
  }
</style>
