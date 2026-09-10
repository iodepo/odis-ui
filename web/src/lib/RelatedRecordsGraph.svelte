<script lang="ts">
  import {
    drag,
    forceCenter,
    forceCollide,
    forceLink,
    forceManyBody,
    forceSimulation,
    select,
    type Simulation,
    type SimulationLinkDatum,
    type SimulationNodeDatum,
  } from "d3";
  import { onDestroy } from "svelte";
  import type { SearchItem } from "./api";
  import { resolveTypeTheme, type TypeThemeKey } from "./typeTheme";

  type Props = {
    source: SearchItem;
    related: SearchItem[];
  };

  let { source, related }: Props = $props();

  const MAX_NODES = 12;
  const WIDTH = 320;
  const HEIGHT = 155;

  type SimNode = SimulationNodeDatum & {
    id: string;
    label: string;
    type: string;
    theme: TypeThemeKey;
    hub: boolean;
    r: number;
  };

  type SimLink = SimulationLinkDatum<SimNode>;

  const TYPE_COLORS: Record<TypeThemeKey, { fill: string; stroke: string }> = {
    dataset: { fill: "var(--dataset-tint)", stroke: "var(--dataset)" },
    literature: { fill: "var(--literature-tint)", stroke: "var(--literature)" },
    org: { fill: "var(--org-tint)", stroke: "var(--org)" },
    training: { fill: "var(--training-tint)", stroke: "var(--training)" },
    project: { fill: "var(--project-tint)", stroke: "var(--project)" },
    default: { fill: "var(--paper-raised)", stroke: "var(--ink-faint)" },
  };

  let svgEl: SVGSVGElement | undefined = $state();
  let overflow = $state(0);
  let legend = $state<{ key: TypeThemeKey; label: string }[]>([]);

  let simulation: Simulation<SimNode, SimLink> | null = null;

  function shortLabel(title: string, max = 18): string {
    const trimmed = title.trim();
    if (trimmed.length <= max) return trimmed;
    return `${trimmed.slice(0, max - 1)}…`;
  }

  function colorFor(theme: TypeThemeKey) {
    return TYPE_COLORS[theme] ?? TYPE_COLORS.default;
  }

  function stopSimulation() {
    simulation?.stop();
    simulation = null;
  }

  $effect(() => {
    const svgNode = svgEl;
    const root = source;
    const hits = related;
    if (!svgNode) return;

    stopSimulation();
    const visible = hits.slice(0, MAX_NODES);
    overflow = Math.max(0, hits.length - MAX_NODES);

    const nodes: SimNode[] = [
      {
        id: root.id,
        label: shortLabel(root.title, 18),
        type: root.type,
        theme: resolveTypeTheme(root.type).key,
        hub: true,
        r: 12,
        x: WIDTH / 2,
        y: HEIGHT / 2,
      },
      ...visible.map((hit, index) => {
        const angle = -Math.PI / 2 + (index * 2 * Math.PI) / Math.max(visible.length, 1);
        return {
          id: hit.id,
          label: shortLabel(hit.title, 14),
          type: hit.type,
          theme: resolveTypeTheme(hit.type).key,
          hub: false,
          r: 8,
          x: WIDTH / 2 + Math.cos(angle) * 52,
          y: HEIGHT / 2 + Math.sin(angle) * 52,
        };
      }),
    ];

    const links: SimLink[] = nodes
      .filter((node) => !node.hub)
      .map((node) => ({ source: root.id, target: node.id }));

    const themeLabels = new Map<TypeThemeKey, string>();
    for (const node of nodes) {
      if (!themeLabels.has(node.theme)) {
        themeLabels.set(node.theme, node.type);
      }
    }
    legend = [...themeLabels.entries()].map(([key, label]) => ({ key, label }));

    const svg = select(svgNode);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    const linkSel = g
      .append("g")
      .attr("class", "related-graph-edges")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("class", "related-graph-edge");

    const nodeSel = g
      .append("g")
      .attr("class", "related-graph-nodes")
      .selectAll("g")
      .data(nodes, (d) => (d as SimNode).id)
      .join("g")
      .attr("class", (d) => (d.hub ? "related-graph-node hub" : "related-graph-node"))
      .call(
        drag<SVGGElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation?.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation?.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }),
      );

    nodeSel
      .append("circle")
      .attr("r", (d) => d.r)
      .attr("fill", (d) => colorFor(d.theme).fill)
      .attr("stroke", (d) => colorFor(d.theme).stroke)
      .attr("stroke-width", (d) => (d.hub ? 2.5 : 1.75));

    nodeSel.append("title").text((d) => `${d.type}: ${d.label}`);

    nodeSel
      .append("text")
      .attr("dy", (d) => d.r + 9)
      .attr("text-anchor", "middle")
      .text((d) => d.label);

    simulation = forceSimulation(nodes)
      .force(
        "link",
        forceLink<SimNode, SimLink>(links)
          .id((d) => d.id)
          .distance(58)
          .strength(0.9),
      )
      .force("charge", forceManyBody().strength(-150))
      .force("center", forceCenter(WIDTH / 2, HEIGHT / 2 - 2))
      .force(
        "collide",
        forceCollide<SimNode>()
          .radius((d) => d.r + 14)
          .strength(0.9),
      )
      .on("tick", () => {
        for (const node of nodes) {
          node.x = Math.max(node.r + 4, Math.min(WIDTH - node.r - 4, node.x ?? 0));
          node.y = Math.max(node.r + 4, Math.min(HEIGHT - node.r - 12, node.y ?? 0));
        }

        linkSel
          .attr("x1", (d) => (d.source as SimNode).x ?? 0)
          .attr("y1", (d) => (d.source as SimNode).y ?? 0)
          .attr("x2", (d) => (d.target as SimNode).x ?? 0)
          .attr("y2", (d) => (d.target as SimNode).y ?? 0);

        nodeSel.attr("transform", (d) => `translate(${d.x ?? 0} ${d.y ?? 0})`);
      });

    return () => {
      stopSimulation();
      svg.selectAll("*").remove();
    };
  });

  onDestroy(() => {
    stopSimulation();
  });
</script>

<figure class="related-graph" aria-label="Related records graph">
  <svg bind:this={svgEl} viewBox="0 0 {WIDTH} {HEIGHT}" role="img">
    <title>Links from {source.title} to related records</title>
  </svg>
  {#if legend.length}
    <ul class="related-graph-legend">
      {#each legend as entry (entry.key)}
        <li>
          <span
            class="related-graph-swatch"
            style="background: {colorFor(entry.key).fill}; border-color: {colorFor(entry.key)
              .stroke}"
          ></span>
          {entry.label}
        </li>
      {/each}
    </ul>
  {/if}
  {#if overflow > 0}
    <figcaption>+{overflow} more in the list below</figcaption>
  {/if}
</figure>
