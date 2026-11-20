# TRADE SIMULATION — ACTIVE BOARD (MAX 60 LINES)

The runner (AI supervisor kit) takes the first `- [ ]` line in **ACTIVE QUEUE**. Nothing runs until the owner says go. Plan and decisions: [`PROJECT.md`](PROJECT.md).

## RULES (details in CLAUDE.md)
- Learning tools go in `tools/`: one standalone HTML file each, no build step, no external scripts.
- No C# project yet. Check a page by reading it back once; check maths with one `node -e` call.
- Never touch `PROJECT.md`, `README.md`, `CLAUDE.md`, `docs/VISION.md`, `archive/`.

## ACTIVE QUEUE (one task per session)
- [ ] **V2:** [model:sonnet] Noise explorer `tools/noise-explorer.html` (new file), a learning tool for `notes/world-formula.md` "Layer 2" (~L71–162: hash ~L80, 1D value noise ~L92, 2D ~L127, octaves ~L139). Three panels: 1D value noise (sliders: size, seed, smoothstep on/off, grid points marked), 2D value noise as a greyscale canvas (size, seed), octaves (count, roughness). Use the notes' exact `hash`. British English. Done when all three panels redraw live from their sliders.

## TOGETHER (owner + Claude in a normal chat, not for the runner)
- Design note 1.0: how the world is made (pipeline, size, units, test region).
- Design note 1.1: height. Finish the noise lessons (2D value noise → octaves → simplex), then a landmass with ocean all round.

## Known failures (not yours)
- none
