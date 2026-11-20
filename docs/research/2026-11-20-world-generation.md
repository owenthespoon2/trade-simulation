# Research: realistic world generation

*20 November 2026. A web research scout (Sonnet) summarised what Dwarf Fortress and procedural-generation research do. **(F)** = found in a source, **(K)** = the scout's background knowledge, **(O)** = opinion. It read search snippets only, so treat the details as leads, not proof.*

## What Dwarf Fortress does

- **Order (F):** elevation (midpoint displacement) → temperature (latitude + height) → rainfall → drainage → biomes, then rivers, lakes, minerals and vegetation, then a check that the world is acceptable. [Advanced world generation](https://dwarffortresswiki.org/index.php/DF2014:Advanced_world_generation)
- **Erosion (F):** only a cliff-smoothing step, not a physical simulation.
- **Rejection (F):** worlds that miss target ranges (too little drainage, too few hills and so on) are thrown away and generated again. [World rejection](https://dwarffortresswiki.org/index.php/40d:World_rejection)
- **Underground (F):**
  - three cavern layers, then a magma sea, with magma pipes rising from it;
  - stone layers follow real geology: sedimentary rock on top, holding shallow metals, then igneous rock deeper down.
  - Sources: [Cavern](https://dwarffortresswiki.org/index.php/Cavern), [Layer](https://dwarffortresswiki.org/index.php/Layer)
- **History (F):** after the land, a strategy-game-like simulation of civilisations runs for hundreds of years. *How it places their origins wasn't found.*

## A recommended pipeline (scout's proposal, 1,024 × 1,024 cells at 1 km)

1. **Tectonic plates:**
   - split the world into plates;
   - where they collide you get mountains and volcanic arcs;
   - where they pull apart you get rifts and trenches.
   - Source: [Red Blob Games, planet generation](https://www.redblobgames.com/x/1843-planet-generation) (K)
2. **Base height:**
   - tectonic uplift, plus layered noise;
   - "ridged" noise for mountain ridges;
   - **domain warping** so coasts aren't blobby.
   - Source: [Terrain from noise](https://www.redblobgames.com/maps/terrain-from-noise/) (K)
3. **Hotspots and volcanoes:** island chains along a line, and volcano arcs behind ocean trenches, as in Japan. (K, O)
4. **Rock type and hardness** for every cell (igneous, sedimentary, metamorphic), from the tectonic setting. (O)
5. **River erosion, the "stream power law":** `dz/dt = U − K·A^m·S^n`
   - the ground rises by uplift U, and is worn down faster where more water flows (A) and the slope is steeper (S);
   - K is softer or harder depending on the rock;
   - 50–200 iterations.
   - Sources: [O'Leary](https://mewo2.com/notes/terrain/) (F); [Cordonnier et al.](https://diglib.eg.org/xmlui/handle/10.1111/cgf12820) (F)
6. **Thermal erosion:** slopes steeper than a scree angle crumble down. A few dozen passes soften cliffs. (K)
7. **Droplet erosion**, optional and only for close-up detail (expensive). (K, O)
8. **Sea level:** pick it so about 30–40% is land, then flood-fill to tell ocean from inland basins. (K)
9. **Rivers and lakes** from one shared drainage graph, so they always agree with the land. (K)
10. **Temperature:** latitude, height, and a milder climate near coasts. (K)
11. **Wind and rain:** moisture is picked up over the sea and dropped on rising ground, leaving a rain shadow behind. Sources: [mapgen4](https://www.redblobgames.com/maps/mapgen4), [wind patterns](https://www.redblobgames.com/x/1731-wind-patterns/) (F)
12. **Ocean currents:** a warm or cold offset for coasts. A cheap fudge. (O)
13. **Biomes:** a Whittaker table, plus drainage. Source: [polygon map generation](https://www.redblobgames.com/maps/polygon-map-generation/) (F)
14. **Ore by geology:**
    - metals near volcanoes and plate edges;
    - coal, iron and salt in sedimentary rock.
    - (K, O)
15. **Underground:**
    - a stack of rock layers per column;
    - caves from 3D noise;
    - a magma depth.
    - Generated only where needed. (K, O)
16. **Rejection tests:** regenerate if land, coast or river targets are missed. (F)
17. **Civilisation origins and history:** score sites for food, water, rivers, coast and resources, then simulate year by year. (O)

## Cost at about 1 million cells (estimates)

| Cheap (< 1 s) | Moderate (seconds to a minute) | Expensive (10 s or more) |
|---|---|---|
| noise, plates, temperature, biomes, ore | filling dips, flow totals, the rain sweep, thermal erosion | 100+ stream-power iterations, droplet erosion, history simulation |

**A 5–10 minute budget covers all of it.**

## Best realism for the effort (scout's ranking, opinion)

1. **Stream-power erosion:** the biggest visual gain, giving branching valleys and believable rivers.
2. Rivers and lakes from one drainage graph.
3. Wind with rain shadows, plus latitude and height temperature.
4. Tectonic plates: real mountain ranges, continent shapes and island arcs instead of noise blobs.
5. Rock hardness changing the erosion: cliffs, plateaus and varied coasts.
6. Thermal erosion (cheap).
7. Ore linked to geology (cheap, and it drives trade).
8. Ocean currents and hotspot island chains (lowest priority).

*Not researched yet: Azgaar's Fantasy Map Generator, WorldEngine and Experilous. DF's exact river carving and civilisation placement are unverified.*
