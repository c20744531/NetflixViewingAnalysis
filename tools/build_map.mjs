// Pre-renders the "where my shows come from" world map to docs/map.svg so
// the page needs no mapping library at runtime.
// Run from the repo root with d3-geo, topojson-client and world-atlas
// installed:  node tools/build_map.mjs
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { geoEqualEarth, geoPath } from "d3-geo";
import { feature } from "topojson-client";

const require = createRequire(import.meta.url);
const world = JSON.parse(readFileSync(require.resolve("world-atlas/countries-110m.json"), "utf8"));
const data = JSON.parse(readFileSync("docs/data.json", "utf8"));
const counts = Object.fromEntries(data.countries.map((c) => [String(Number(c.iso)), c]));

const W = 960, H = 470;
const countries = feature(world, world.objects.countries).features.filter((f) => f.id !== "010"); // drop Antarctica
const projection = geoEqualEarth().fitSize([W, H], { type: "FeatureCollection", features: countries });
const path = geoPath(projection);

const step = (n) => (n >= 11 ? 4 : n >= 4 ? 3 : n >= 2 ? 2 : 1);

const shapes = countries.map((f) => {
  const c = counts[String(Number(f.id))];
  const d = path(f);
  if (!d) return "";
  return c
    ? `<path class="m${step(c.titles)}" d="${d}" data-country="${c.country}" data-titles="${c.titles}"><title>${c.country}: ${c.titles} title${c.titles > 1 ? "s" : ""}</title></path>`
    : `<path d="${d}"/>`;
});

writeFileSync(
  "docs/map.svg",
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="World map of where the titles I watched were made">${shapes.join("")}</svg>`,
);
console.log("wrote docs/map.svg");
