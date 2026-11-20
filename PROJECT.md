# Project file

*Last updated: 20 November 2026 · **Restarted** on this date*

**Read this first when you come back.** The top section says what we're doing and what's next. The game itself is described in [`docs/VISION.md`](docs/VISION.md). Updated at the end of every session.

---

# 📍 NOW

**Phase: Stage 1, the world.** The plan is settled and the world pipeline is agreed ([note 1.0](docs/design/1.0-how-the-world-is-made.md)). Next is note 1.1, height. No code yet.

**Where things stand:**
- **The game is defined:** a fantasy medieval world where you play a wandering trader who works their way up. See [`docs/VISION.md`](docs/VISION.md).
- **The language is chosen: C# / .NET.** Claude writes the code; you understand every piece through design notes before it's built.
- The September work (Python prototype, 200 km lake world, TypeScript plan) is in [`archive/`](archive/). The noise maths in [`notes/world-formula.md`](notes/world-formula.md) carries over.

## Next steps

| # | Step | Who | Status |
|---|---|---|---|
| 1 | Read [`docs/VISION.md`](docs/VISION.md) and correct anything that's wrong or missing | You | any time |
| 2 | Install the free **.NET SDK** | Claude | ✅ .NET 10 (long-term support) installed 20 Nov |
| 3 | **[Design note 1.0: how the world is made](docs/design/1.0-how-the-world-is-made.md).** The whole world-generation pipeline on one page: height → temperature → rain → rivers → fertility → biomes, the world's size, units and the size of the test region. All five proposals agreed | Together | ✅ understood 20 Nov |
| 4 | **Design note 1.1: height.** Finish the noise lessons (2D value noise, octaves, simplex), then shape a landmass with ocean around it | Together | ▶ now |
| 5 | Build 1.0 + 1.1 in C#, with a first map picture | Claude, after you understand the notes | after 4 |

## Resume quickly

1. In `C:\Projects\trade-system-prototype`, run `git pull`.
2. Read **NOW** above, then the newest design note in [`docs/design/`](docs/design/README.md).
3. Tell Claude which step to continue.

---

# 🧭 How we work

Every system goes through the same five steps:

1. **Design note first.** Claude writes `docs/design/<n>-<name>.md`: what the system does, the maths, the logic, worked examples with real numbers, and what was simplified.
2. **Understand it.** We go through the note together. Questions and corrections go into the note. **We don't move on until it makes sense to you.**
3. **Build it.** Claude writes the C# code and tests, following the note exactly.
4. **Check it.** Run it, look at the numbers and a picture, and compare them with the note's worked examples.
5. **The note stays** as the explanation of that code. If the code changes, the note changes with it.

Other habits:
- **One branch and one pull request per piece of work.** `main` always works.
- **Small, well-defined jobs** (an explorer page, a test, a tidy-up) go on [`BOARD.md`](BOARD.md) and can run unattended with the AI supervisor kit, on cheaper models.

---

# 🗺 Roadmap

Each stage ends with something you can run and look at. Early stages are deliberately simple; realism is added stage by stage. **Part A, the simulated world, comes first.** The player arrives in Part B, once the world runs well on its own.

### Part A: a world that runs by itself

| Stage | What | You'll be able to |
|---|---|---|
| **0** | **Restart and plan:** vision, roadmap, language, way of working | Read the plan ✅ |
| **1** | **The surface world, first version**, on a small test region ▶ *now* | See the world as a pixel map |
| | 1.1 height (noise, landmass, ocean all round, simple islands) | |
| | 1.2 temperature · 1.3 rain · 1.4 rivers and lakes · 1.5 fertility and biomes · 1.6 map viewer | |
| **2** | **The realistic world generator** *(proposed)*: tectonic plates, volcanoes and island arcs, rock hardness, river and slope erosion, ocean currents, rejection of bad worlds. Allowed to take 5–10 minutes | Watch valleys carve and islands form |
| **3** | **The underground:** rock layers, ore by geology, caves and caverns, magma | See where the dwarves will dig |
| **4** | **Peoples and history:** origin homelands for humans, elves and dwarves; years of coarse history at world generation (founding, colonies, expansion) | See a world map with a history |
| **5** | **Produce and eat:** settlements as groups of people (pops), goods, recipes, the food maths; animals and hunting | Watch each settlement feed itself, or fail to |
| **6** | **Markets and money:** prices from supply and demand, conserved money, barter and credit in hamlets, coin in towns | See prices differ from region to region |
| **7** | **Traders, routes and transport:** AI traders that find their way, boats on rivers and the sea, paths becoming roads | Watch caravans and boats move, and roads appear |
| **8** | **A world that changes:** seasons and weather, bad harvests, settlements growing and shrinking, new colonies founded, all regions always running | Leave it running and watch where it goes |

**The success test for stages 5–8** (carried over from the Python prototype): years of game time, nobody starves, money stays constant, and prices move within a range rather than drifting away.

### Part B: the game

| Stage | What |
|---|---|
| **9** | **Levels of detail:** zoom from world (1 km) to region (100 m) to town (1 m), generated when needed, while the rest of the world keeps running |
| **10** | **The player:** a trader on foot, buying and selling; solve the time-scale problem |
| **11** | **Growing up:** horse, cart, caravan, hired traders, a company |
| **12** | **Settle down:** property, influence, local government |
| **13** | **Looks:** proper pixel-art top-down view |
| Later | Scale up to a Japan-sized country, more species, foreign ports, local AI for names, chronicles and dialogue |

---

# ✅ Decisions

## Made at the restart (20 Nov 2026)

| Decision | Why |
|---|---|
| **Fantasy medieval world**; the player is a **trader** who starts on foot and works up | More personal and more fun than playing a settlement. The world itself is the star |
| **C# / .NET**, Rust as fallback for top speed | Near-Rust speed, an AI writes it very well, and it's readable for you. Research compared Rust, C#, C++, Go, Julia, TypeScript, Python, Zig and Odin |
| **Claude writes the code; design notes first, and you must understand before we build** | You want to understand all the maths and logic, without spending your time typing code |
| **World first**, starting with a small test region and growing towards a Japan-sized country | The world is the most maths-heavy part and everything else sits on it |
| **Biomes come from height, temperature, rain and rivers**, never painted by hand | So the world is consistent and different every seed |
| **Restart the docs**; September's plan archived | The repo should show where we are now |
| **Research and scouting run on cheaper models** (Sonnet/Haiku) | Saves tokens. Opus only for hard design |
| **World pipeline: height → temperature → rain → rivers and lakes → fertility and biomes** ([note 1.0](docs/design/1.0-how-the-world-is-made.md)) | Each step only uses the ones before it, like Dwarf Fortress' world generation |
| **Height stays a formula; climate and rivers live on a 1 km grid**, calculated once when the world is made | Rivers and rain depend on everything uphill or upwind, so they need the whole map at once |
| **Final world 1,024 × 1,024 km** (about Japan's land area); **test region 256 × 256 km** with a squashed climate | Small enough to try many seeds fast; scale up once it works |
| **Climate:** about −2 °C in the far north, about 22 °C in the far south, 6.5 °C colder per 1,000 m, wind from the west | Cold north and warm south give the range of biomes we want |
| **Simulation first, player last; PC only** | You want a realistic world that runs on its own and to watch it develop, before any game is added |
| **Humans, elves and dwarves** as the main races, each with a homeland, founding colonies | Different races in different lands give different economies |
| **World generation may take 5–10 minutes** if that buys realism (erosion, geology, volcanoes) | Realism-game players are happy to wait |
| **Underground after the surface**: caves, ore, magma | Dwarves need it, but it's built on the surface world |
| **Local AI only for words** (names, chronicles, dialogue), never for simulation decisions | Too slow at ~16 tokens a second; rules are faster, repeatable and understood |

## Carried over from September

| Decision | Why |
|---|---|
| **The land is a formula**: height at any point is calculated; only changes (fields, roads) are stored | Detail is free, and any point can be found with maths |
| **Money is conserved**: only ever moved, never created or destroyed by accident | The Python prototype lost two-thirds of its money this way |
| **Real units**: distances in km, heights in metres, 1 tick = 1 day (to be revisited with the time-scale problem) | Every number can be sanity-checked |
| **The numbers are the truth; pictures are drawn from them** | A detailed town view can come later without rewriting the simulation |
| **Every piece of work gets its own branch and PR** | Keeps `main` working, and shows what changed and why |
| **Python prototype kept as reference** at the tag `python-prototype` | Read it when stuck, don't port it |

---

# 📚 Where things are

| | |
|---|---|
| [`docs/VISION.md`](docs/VISION.md) | ⭐ The game: world, civilisations, economy, the player, the time problem |
| `docs/design/` | Design notes, one per system, written before each is built (starts with note 1.0) |
| [`notes/world-formula.md`](notes/world-formula.md) | Maths lessons so far: smoothstep, the hash, value noise |
| [`docs/research/`](docs/research/) | Research reports, dated: world generation, living-world simulation |
| [`BOARD.md`](BOARD.md) | Small jobs for unattended AI runs |
| [`archive/2026-09-plan/`](archive/2026-09-plan/PROJECT-2026-09.md) | The September plan: 200 km lake world, three towns, TypeScript |
| [`archive/python-prototype/`](archive/python-prototype/README.md) | The original Python prototype and what it taught us |
| Obsidian / Drive | Older design docs (see the September plan's list; the Obsidian vault has duplicate copies) |

---

# 📓 Session log

### 20 November 2026: the restart
- Came back after two months. Set the project up for the AI supervisor kit (board, rules, helper agents).
- Researched languages: **C#** chosen, Rust as fallback.
- Defined the game: a fantasy medieval trader game in a living world, inspired by Dwarf Fortress and RimWorld. Written up in [`docs/VISION.md`](docs/VISION.md).
- New way of working: design note → you understand → Claude builds → the note stays.
- Archived the September plan and rewrote this file, the README and the roadmap.
- Installed the .NET 10 SDK.
- **Design note 1.0 agreed:** the world pipeline, formula plus 1 km grid, world and test-region sizes, climate range, and a first biome table. Stage 1 begins.
- Started note 1.1 (height): lesson A, 2D value noise, with a slower step-by-step explanation and a side note on finite element shape functions.
- New ideas recorded in [`docs/VISION.md`](docs/VISION.md): simulation first, player last; realistic slow world generation; the underground; humans, elves and dwarves with homelands; islands; boats; animals; levels of detail; local AI. Two research reports in [`docs/research/`](docs/research/). Roadmap reordered into Part A (the world) and Part B (the game).

### Before the restart
See [`archive/2026-09-plan/PROJECT-2026-09.md`](archive/2026-09-plan/PROJECT-2026-09.md#-session-log) (18–19 September 2026: Python fixes, three-town design, the 200 km world, the first noise lessons).

---

# ✏ Keeping this file current

At the end of each session: update **Last updated**, **NOW**, new **decisions**, the **session log**, and tick the **roadmap**. Then update the **Latest update** box in [`README.md`](README.md).

**Git in one line:** new branch → commit → push → pull request → you review **Files changed** → **Merge** → `git pull` in your folder.
