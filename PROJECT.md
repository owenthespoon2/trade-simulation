# Project file

*Last updated: 21 November 2026 (foundation planned) · **Restarted** 20 November 2026*

**Read this first when you come back.** The top section says what we're doing and what's next. The game itself is described in [`docs/VISION.md`](docs/VISION.md). Updated at the end of every session. **Any AI picking this up (Claude or not): read [`AGENTS.md`](AGENTS.md) first.**

---

# 📍 NOW

**Phase: foundation planned; next it gets built in `evolution-sandbox`.** The world pipeline is agreed ([note 1.0](docs/design/1.0-how-the-world-is-made.md)), note 1.1 (height) has its first lesson, and the agents and economy are brainstormed ([note 4.0](docs/design/4.0-agents-brainstorm.md)). No code yet.

**Where things stand:**
- **The vision is big and written down:** a fantasy medieval world that runs by itself (humans, elves and dwarves; factions and kingdoms; an economy; traders and boats; people reshaping the land; magic later), with the player coming last. See [`docs/VISION.md`](docs/VISION.md).
- **The agents are brainstormed** (20 Nov): every person named with a family tree, **families decide**, every trader tracked, prices that **emerge** from agents' beliefs, **dwarves mint the money**, and two decision modes: scoring first, then **evolving neural networks** (the favourite idea). Summary in [VISION section 13](docs/VISION.md#13-agents-and-the-economy).
- **The foundation is agreed** (21 Nov), in [evolution-sandbox's design note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md): **MonoGame** for graphics (+ Dear ImGui panels, Myra or our own menus later), **headless first** with one simulation library and two front ends, save/load from day one, parallel steps inside a tick, events in Parquet/DuckDB, **Python** for reports and analysis. A reusable **Foundation** library will come into this repo as a **git submodule**. Summary in [VISION section 8](docs/VISION.md#8-how-its-built).
- **Next conversation:** build evolution-sandbox **milestone 0** (speed test first), in that repository.
- **The language is chosen: C# / .NET.** Claude writes the code; you understand every piece through design notes before it's built.
- The September work (Python prototype, 200 km lake world, TypeScript plan) is in [`archive/`](archive/). The noise maths in [`notes/world-formula.md`](notes/world-formula.md) carries over.

## Next steps

| # | Step | Who | Status |
|---|---|---|---|
| 1 | Read [`docs/VISION.md`](docs/VISION.md) and correct anything that's wrong or missing | You | any time |
| 2 | Install the free **.NET SDK** | Claude | ✅ .NET 10 (long-term support) installed 20 Nov |
| 3 | **[Design note 1.0: how the world is made](docs/design/1.0-how-the-world-is-made.md).** The whole world-generation pipeline on one page: height → temperature → rain → rivers → fertility → biomes, the world's size, units and the size of the test region. All five proposals agreed | Together | ✅ understood 20 Nov |
| 4 | **Brainstorm the agents**: who they are, what they strive for, how they decide, groups and individuals, the economy. [Note 4.0](docs/design/4.0-agents-brainstorm.md), [VISION section 13](docs/VISION.md#13-agents-and-the-economy) | Together | ✅ 20 Nov (goods and recipes, changing the world and running cheaply still to do) |
| 5 | **The foundation** (new chat): engine or graphics library, **headless mode first**, how agents are stored and drawn, main loop, statistics. Planned in the [`evolution-sandbox`](https://github.com/owenthespoon2/evolution-sandbox) repository ([note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md)) | Together | ✅ 21 Nov |
| 6 | **Build evolution-sandbox milestone 0** (speed test, headless runs, window, data), then neural network lessons and **milestone 1** (creatures learn to find food) | AI, after you understand the notes | ▶ next chat |
| 7 | **Design note 1.1: height.** Lesson A (2D value noise) done; next lesson B, octaves; then simplex, the landmass, mountain ranges | Together | after 5 |
| 8 | Build 1.0 + 1.1 in C# on the foundation, with a first map picture | Claude, after you understand the notes | after 7 |
| 9 | **Second agents brainstorm:** goods and recipes, how agents change the world, keeping it cheap to run | Together | any time |

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
| **4** | **Peoples and history:** origin homelands for humans, elves and dwarves; years of coarse history at world generation (founding, colonies, expansion); factions growing into kingdoms with lords beneath them | See a world map with a history and borders |
| **5** | **Produce and eat:** settlements as groups of people (pops), goods, recipes, the food maths; animals and hunting | Watch each settlement feed itself, or fail to |
| **6** | **Markets and money:** prices from supply and demand, conserved money, barter and credit in hamlets, coin in towns | See prices differ from region to region |
| **7** | **Traders, routes and transport:** AI traders that find their way, travel speed by terrain, boats on rivers and the sea, paths becoming roads | Watch caravans and boats move, and roads appear |
| **8** | **A world that changes:** seasons and weather, bad harvests, forests felled and regrowing, simple construction (houses, markets, ports, taverns), ideas spreading along routes, settlements growing and shrinking, new colonies, politics | Leave it running and watch where it goes |

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
| **One currency for now** | Several currencies would be realistic but much harder |
| **Construction stays simple**: towns have houses, markets, ports and so on, but this is not a colony builder | Realistic towns without turning the project into a different game |
| **Magic: yes, but later.** Hooks now (aptitudes, goods and races as data, a magic map layer, spreading knowledge); the system itself after the world and economy work | Magic makes the world richer but can break the economy; hooks cost almost nothing now |
| **Masses as groups, notable people as individuals** (like Dwarf Fortress' historical figures) | Storage is easy; decisions are the expensive part |
| **Design wide, build narrow** | Plan room for everything, but switch on one system at a time so it can be debugged |

## Made in the agents brainstorm (20 Nov 2026)

| Decision | Why |
|---|---|
| **Every person stored** (name, race, parents, skills, family tree); **the family decides**; pops are totals | Storing people is cheap; decisions are the expensive part |
| **Marriages, children and inheritance** simulated; inheritance rules differ by race | Links villages and kingdoms; landless younger children found new villages |
| **Every trader tracked as an individual**; notable people step out of their families | Traders are the heart of the game |
| **Two decision modes:** scoring (utility AI) built first; **evolving neural networks** (neuroevolution) as the second, favourite mode | Scoring is explainable and a baseline; emergence from evolution is the owner's deepest interest |
| **Personalities for every family**, inherited; **habit**; **limited knowledge** (only news that has reached you) | Different people make different stories; stops the world flipping back and forth |
| **Prices emerge from agents' price beliefs** on **market days** chosen by lords; wages the same way | The economy should come out of the agents, not from formulas |
| **Money minted from silver and gold, at first only by the dwarves** | A unique role for the dwarves, and politics straight out of economics |
| **Banks** for merchants and kings; **every trade recorded** with statistics viewers | Realistic, and the owner loves statistics |
| **Only humans, elves and dwarves at first**; no orcs or lizardfolk; **no serfdom** for now | Design wide, build narrow; fantasy, not too realistic |
| "Local AI only for words" **softened**: never for the masses, maybe for a few notables' big decisions, always recorded | Too slow for the masses, and language models aren't repeatable |
| **A separate test repository, `evolution-sandbox`, builds the foundation** (engine, graphics, agents, statistics) before the world code | Test the base and neuroevolution on something small first |
| **Headless mode in both projects**: no window, console only, full speed | Much faster, and the way to test the simulation; the simulation never depends on the graphics |

## Made in the foundation chat (21 Nov 2026), detail in [evolution-sandbox note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md)

| Decision | Why |
|---|---|
| **MonoGame** + Dear ImGui/ImPlot now, **Myra or our own UI** for the game's menus later | We own the loop; very active; proven by Stardew Valley and Celeste. Raylib-cs is only passively maintained; Godot owns the loop |
| **One simulation library, separate front ends;** outside changes are commands applied between ticks | The front end could be replaced (e.g. by Godot) without a rewrite |
| **Data:** counted actions, meaningful events (every trade) in **Parquet + DuckDB**, agents' **reasons** logged in scoring mode | "Log everything" would be billions of rows; reasons answer "why did they trade this?" |
| **Python** for reports and analysis | The research standard; C# only writes data |
| **Parallel steps inside a tick** for this one big world (read anything, write only your own slot) | Uses the 6 cores while staying repeatable: about 3–5× faster |
| Storage per system (array of records or plain arrays) **chosen with a speed test** | A million people with simple daily loops may want plain arrays |
| The **Foundation** library comes in as a **git submodule** pinned to a version | Reuse without copying; no access keys |
| **Neuroevolution first; reinforcement learning (and imitation learning from the scoring AI) later**, likely the trade sim's neural mode | A reward can fairly describe what people want here |

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
- More ideas recorded: factions growing into kingdoms with lords beneath them (one currency for now); people reshaping the land (simple construction, forests felled and replanted, dams, ports, taverns); travel speed by terrain; lessons from history (Rome–Egypt grain ships, the Silk Road, ideas spreading along routes); a checklist of what the world generator still needs; a first sketch of the simulation's ten layers.
- Magic decided: yes, added later, with hooks built in from the start (aptitudes, goods and races as data, a magic map layer, spreading knowledge). Tree species by biome. Individuals versus groups worked out: a million people fit easily; masses as groups, notable people as individuals. Magic research report in [`docs/research/`](docs/research/).
- Last ideas of the day: a full "scientific" magic system (runes, magic items, research) rather than Skyrim-style combat magic; no general flight magic, only rare creatures like giant mountain falcons; creatures in the caves. **Stopped here.** Next: brainstorm the agents in a fresh chat, then lesson B (octaves).

### 20 November 2026 (later): the agents brainstorm
- Think-tank session on the simulation's agents, written up in [note 4.0](docs/design/4.0-agents-brainstorm.md) and [VISION section 13](docs/VISION.md#13-agents-and-the-economy).
- Agreed: agents versus things; every person named with a family tree; families decide; marriages, children, inheritance; notable people; every trader tracked; settlements, lords, factions, guilds, monasteries and bandits (who can go straight); races organised differently; religion as a future layer; no serfdom.
- Agreed: a ladder of needs, scoring with personality and habit, limited knowledge, memories; the economy emerging from price beliefs on market days; **the dwarves mint the money**; banks; every trade recorded.
- Two research reports: [neural networks and local AI for decisions](docs/research/2026-11-20-neural-agents.md), and [evolving agents and emergent behaviour](docs/research/2026-11-20-emergent-evolution.md). The owner's favourite idea: **evolving neural networks**, with emergent trade as a real research question.
- Decided: a separate repository, [`evolution-sandbox`](https://github.com/owenthespoon2/evolution-sandbox), to build the foundation (engine, graphics, headless mode) with a toy world of evolving creatures. Created with its starting docs. **Next chat: the foundation.**

### 21 November 2026: the foundation chat
- Planned the foundation in [`evolution-sandbox`](https://github.com/owenthespoon2/evolution-sandbox) ([note 0](https://github.com/owenthespoon2/evolution-sandbox/blob/main/docs/design/0-foundation.md)). A Sonnet researcher checked the engines; the choice moved from Raylib-cs to **MonoGame** on the evidence.
- Recorded the foundation in [VISION section 8](docs/VISION.md#8-how-its-built), and RL and imitation learning in section 13.
- Added [`AGENTS.md`](AGENTS.md) so a non-Claude AI can continue with the same way of working (cheap helper agents for scouting and research).

### Before the restart
See [`archive/2026-09-plan/PROJECT-2026-09.md`](archive/2026-09-plan/PROJECT-2026-09.md#-session-log) (18–19 September 2026: Python fixes, three-town design, the 200 km world, the first noise lessons).

---

# ✏ Keeping this file current

At the end of each session: update **Last updated**, **NOW**, new **decisions**, the **session log**, and tick the **roadmap**. Then update the **Latest update** box in [`README.md`](README.md).

**Git in one line:** new branch → commit → push → pull request → you review **Files changed** → **Merge** → `git pull` in your folder.
