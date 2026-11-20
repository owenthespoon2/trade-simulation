# TRADE SIMULATION — ACTIVE BOARD (MAX 60 LINES)

The runner (AI supervisor kit) takes the first `- [ ]` line in **ACTIVE QUEUE**. Nothing runs until the owner says go. Big picture and decisions: [`PROJECT.md`](PROJECT.md).

## RULES (details in CLAUDE.md)
- Standalone pages in `tools/`: one HTML file each, no build step, no external scripts.
- No tests or TypeScript project yet. Check a page by opening it, or with `node` for the maths.
- Never touch `PROJECT.md`, `CLAUDE.md`, `archive/`.

## ACTIVE QUEUE (one task per session)
- [ ] **V1:** [model:sonnet] Rebuild the Layer 1 map explorer as `tools/layer1-map.html` (new file). Formula: `PROJECT.md` "Layer 1" (~L104–118): `height = plain(y) + hills(y) − lakeDip(x, y)`, world −100..100 km both ways, lake surface ~60 m. Draw a 400×400 canvas coloured by height (sea below 0 m, lake below 60 m inside r < 20, green lowlands → brown hills), hover shows x, y, height; plus a north–south cross-section along a chosen x (slider, default 0). British English. Done when opening the file shows the map, the lake in the centre and the coast at y = −80.
- [ ] **V2:** [model:sonnet] Noise explorer `tools/noise-explorer.html` (new file), following `notes/world-formula.md` "Layer 2" (~L69–160: hash ~L78, 1D value noise ~L90, 2D ~L125, octaves ~L137). Three panels: 1D value noise (sliders: size, seed, smoothstep on/off, grid points marked), 2D value noise as a greyscale canvas (size, seed), octaves (count, roughness). Use the notes' exact `hash`. Done when all three panels redraw live from their sliders.

## TOGETHER (owner + Claude in a normal chat, not for the runner)
- Layer 2 lessons: 2D value noise → octaves → Perlin/simplex → noise on our map (see "Where we stopped" in `notes/world-formula.md`).
- Then Layer 3 (rivers), Layer 4 (terrain), then step 3a in TypeScript.

## Known failures (not yours)
- none
