# Trade Simulation: project file

*Last updated: 19 September 2026*

**Read this first when you come back.** The top section says what we're doing and what's next. Everything below it is background. It gets updated at the end of every session.

---

# 📍 NOW

**Focus:** work out the **world formula**, the maths that gives the height of the land at any point, one layer at a time, understanding each part before moving on.

**Where things stand:**
- The **[world design](#-the-world) is confirmed**: a 200 × 200 km world described by a formula, with a central lake, hills to the north, forest to the west, the sea to the south, and one straight river running north to south through the lake.
- The Python prototype is **finished and frozen** at the git tag `python-prototype`. Notes on every file are in [`notes/`](notes/README.md).

## Next steps

| # | Step | Who | Status |
|---|---|---|---|
| 1 | **Design the [world formula](#the-formula) together**, layer by layer. Layer 1 (the big shape) is done; **Layer 2 (noise)** is next, then rivers, then terrain | Together | ▶ now |
| 2 | **Build step 3a** in TypeScript: the formula, plus a page that draws the map. (Node.js v23 is already installed) | Together | after 1 |
| 3 | **Step 3b**: three towns as patches of 1-hectare tiles around the lake | Together | later |
| 4 | **Step 3c**: produce and eat, with the three-town numbers redone for fish and land | Together | later |
| — | Read the [notes](notes/README.md) on the Python code, whenever you have time | You | ongoing |

## Resume quickly

```bash
git pull
python ui_main.py --headless --ticks 200 --print_interval 20
```

---

# ✅ Decisions so far

| Date | Decision | Why |
|---|---|---|
| 18 Sep 2026 | **Wealth is a conserved currency:** never created or destroyed after setup, only moved | Wealth should one day be a real item (coins). The old code deleted money every tick |
| 18 Sep 2026 | **Rewrite in TypeScript**, starting from a new tiny core, not a port | One language for server, web and Telegram. Small code you understand beats porting ten modules |
| 18 Sep 2026 | **Three towns first, everything else off** (migration, abandonment, population growth, market upgrades, storage limits) | You can't debug six feedback loops at once. Switch them back on one at a time |
| 18 Sep 2026 | **Each town has its own kind of food** (grain, meat), and one has none | More realistic than one food town, and still forces trade |
| 18 Sep 2026 | **Python kept as reference**, frozen at tag `python-prototype` | Read it when stuck, don't copy from it |
| 18 Sep 2026 | **Every piece of work gets its own branch and PR** | Keeps `main` working, and shows what changed and why |
| 19 Sep 2026 | **Terrain belongs to the world, not the settlement.** Settlements sit at real positions on a map | So caravans travel across real land, and where a town sits decides what it can make |
| 19 Sep 2026 | **The land is a formula**: height at any (x, y) is calculated, not stored. Only changes (fields, roads, flattened ground) are stored, on top | No fixed tile size, so detail is free and any point can be found with maths |
| 19 Sep 2026 | **Height first**, and terrain worked out from it | Needed for farms on flat ground, and later for rivers and rain |
| 19 Sep 2026 | **1 unit = 1 km, 1 tick = 1 day**, world 200 × 200 km with (0, 0) in the centre | Every number means something you can sanity-check |
| 19 Sep 2026 | **Settlements are patches of 1-hectare land tiles** (town, fields), with a **work area** within walking distance | Settlements look like settlements, and land limits food instead of an arbitrary setting |
| 19 Sep 2026 | **Caravans plan with A\* on a 1 km grid, and remember routes** once used a set number of times | A* on a fine grid would be too slow; remembered routes scale |
| 19 Sep 2026 | **Fishing and boats exist**, added at step 7 after trade works | One system at a time |
| 19 Sep 2026 | **The numbers are the truth; pictures are drawn from them** | So a zoomed-in view (houses, market square, roads) can come later without rewriting the simulation |
| 19 Sep 2026 | **Hills and mountains to the north; one straight river along x = 0**, from the hills into the lake and on to the sea | Flat lowlands around the lake and to the sea, with the real height in the north. One straight river is simple to carve |
| 19 Sep 2026 | **Layer 1 numbers:** lake about a day's walk across, north edge about 840 m, coast at y = −80, 1 m per km slope | A day's walk suits trade; hills of that size look big from afar |
| 19 Sep 2026 | **Hillfort sits at the foot of the hills**, a little back from the shore | Hills (and later mines) within its work area |

---

# 🌍 The world

*Confirmed 19 September 2026 (hills moved to the north the same day). Layer 1 of the formula is settled; the rest is being worked out.*

**A 200 × 200 km world, described by a formula.** (0, 0) is the centre, x runs west → east, y runs south → north, 1 unit = 1 km, and 1 tick = 1 day.

### Layout

Sketch, not to scale:

```
 N ↑   ^ ^ ^ ^ ^ ^ ^ ^ ≈ ^ ^ ^ ^ ^ ^ ^ ^    mountains, continuing off the map
       n n n n n n n n ≈ n n n n n n n n    hills
       T T T T T . . H ≈ . . . . . . . .    H Hillfort: at the foot of the hills, by River 1
       T T T T . . . ~ ~ ~ . . . . . . .
       T T T W ~ ~ ~ ~ ~ ~ ~ . . . . . .    W Woodhaven: west shore, in the forest
       T T T . . ~ ~ ~ ~ ~ . . . . . . .
       T T . . . . . F ≈ . . . . . . . .    F Farmstead: south shore, at the outlet
       . . . . . . . . ≈ . . . . . . . .
       . . . . . . . . ≈ . . . . . . . .    flat farmland, sloping gently south
       ~ ~ ~ ~ ~ ~ ~ ~ ≈ ~ ~ ~ ~ ~ ~ ~ ~    sea

       T forest   . grassland   n hills   ^ mountains   ~ water   ≈ river
```

- **North:** hills rising into a mountain range that continues beyond the map. The north edge is about 840 m high (Yahiko is 634 m).
- **River 1** comes down from the northern hills and runs straight south along x = 0 into the lake.
- **Centre:** the lake, about 28 km from shore to shore, so about a day's walk. That's roughly Lake Biwa's width.
- **River 2** drains the lake straight south along x = 0 to the sea. Lakes with an inflow need an outflow, or they turn salty, and it links the lake to the sea for boats.
- **South:** flat farmland sloping gently (1 m per km) to the sea, with the coast at y = −80.
- **West and north-west:** forest. **East:** open farmland, room to grow.
- **Towns:** Hillfort at the foot of the hills north of the lake, by River 1 (mines later); Woodhaven on the west shore in the forest; Farmstead on the south shore at the outlet.

### The formula

Built in layers, each understood before the next:

| Layer | What | Status |
|---|---|---|
| 0 | Units: height in metres, sea level 0 m, below 0 is underwater | ✅ |
| 1 | The big shape: slope to the sea, northern hills, lake dip | ✅ settled 19 Sep |
| 2 | Noise: natural bumps; the coast and lake shore wiggle automatically | ▶ next |
| 3 | Rivers: two grooves along x = 0 whose beds always run downhill | |
| 4 | Terrain from height, slope and a forest map | |

**Layer 1:**

```
height(x, y) = plain(y) + hills(y) − lakeDip(x, y)

plain(y)    = 1 × (y + 80)                     rises 1 m per km north; coast at y = −80
hills(y)    = 1500 × smoothstep(15, 200, y)    starts at y = 15, peaks off the map at y = 200
lakeDip     = 63 × (1 − smoothstep(0, 20, r))  r = √(x² + y²), distance from the centre

smoothstep(a, b, v): t = (v − a) / (b − a), kept between 0 and 1; result = t × t × (3 − 2t)
```

- The lake fills its dip until it spills over the lowest point of the rim. Because the land slopes south, that point is on the south side, exactly where River 2 leaves.
- The lake surface is at about 60 m and the lake is about 44 m deep.
- A lake only forms if the dip is deeper than slope × radius (63 m against 1 × 20 = 20 m).

### Detail: each part uses what it needs

Because the land is a formula, there's no single tile size. Only *changes* to the land are stored, where they happen:

> actual height = formula height + changes

| Part | Detail |
|---|---|
| Land shape (height, terrain) | The formula: any detail, nothing stored |
| Land use: town, fields, roads | 100 m tiles (1 hectare), stored only around settlements. A 100-person village is ~100 field tiles plus a few town tiles |
| Houses, market square | ~10 m, in a zoomed-in settlement view (later) |
| Route planning (A*) | 1 km grid |
| Water flowing, rain (later) | A coarse grid |
| Map viewer | Whatever the screen needs |

**Rivers:** the first two are *designed*, as channels cut into the formula. Rivers that *emerge* from rain need water flowing across the whole map, which is a grid simulation, so that comes later.

### Settlements

- A **patch of 1-hectare tiles**, each with a job: **town** or **field** (later also pasture, woodland, mine, road).
- **Fields only on flat ground**; later, people can flatten land (terracing).
- **Work area:** land within walking distance of the edge of town. Bigger towns reach further. When flat land in reach runs out, food stops growing: trade, or people leave to found a new town.
- **The numbers are the truth; pictures are drawn from them.**

### Caravans and routes

1. **Plan coarse, walk fine:** A* on the 1 km grid (40,000 tiles). You'll write the A* yourself, starting on a 10×10 grid.
2. **Remember routes:** after a set number of trips, a route becomes an **established trade route** and is followed without planning again, unless the land changes.
3. **Routes become roads (later):** heavy use wears tracks into roads, roads are faster, and faster roads attract traffic.

### Fishing, boats and the sea

- **Fishing** from shore tiles, needs tools. The lake has a **shared fish stock that regrows slowly**, so overfishing collapses it.
- **Boats** from wood and tools: lake fishing first, then river and coast trade.
- **The outside world (later):** a port and foreign ships. Foreign traders carry their own money, so money entering the world is deliberate and counted.

---

# 🔍 What the Python prototype taught us

We ran it headless, measured, and found **three separate problems**, each hiding the next.

### 1. Money was being destroyed ✅ fixed (PR #1)

Total wealth fell from 5,000 to 1,796 by tick 98. It was deleted in three places and never paid to anyone:

| Leak | Share |
|---|---|
| Transport cost: the buyer paid it, nobody received it | 55% |
| Storage upkeep | 34% |
| Tool recipe fee | 11% |

**Fix:** every payment goes through `transfer_wealth()`, and a check warns any tick the total drifts. Tested on 5 random seeds: total stays at exactly 5,000.

### 2. The world can't feed itself ❌ not fixed

With all money leaks off, everyone *still* starves by tick 90–115. The world makes about **20 food per tick and eats about 50**:
- Each recipe can only run 5 times per tick (`max_production_passes`).
- One person's work grows exactly the grain one person eats, leaving no surplus.
- Only 2 of 5 towns can farm.
- Hungry people eat *more* (up to 3×).

In experiments, making labour the only limit, doubling grain yield and stopping hunger-overeating let the world survive 1,000 ticks. But see problem 3.

### 3. Money pools with the food seller ❌ not fixed

Once there's enough food, all 5,000 wealth ends up in the grain town, and the others starve broke. Only bread and grain have any **demand** in the price formula, so wood, iron and tools sell at the price floor. Everyone pays full price for food and earns nothing back.

### The lessons for the rewrite

1. **Conserve money from day one.** Transfers only, with a check every tick.
2. **Do the food maths on paper first:** food made ≥ food eaten, with slack.
3. **Every town needs something it sells continuously.** Things that get used up (food, firewood, tools that wear out) create steady demand; things that last forever don't.
4. **Demand must include recipe inputs**, not just food.
5. **Measure before fixing.** Printing one number (total wealth per tick) settled a week of guessing.

More detail, including smaller problems: [`notes/trade_logic.md` § Known problems](notes/trade_logic.md#5-known-problems-summary).

**What success looks like for the new version:** 1,000 ticks, nobody starves, total wealth flat, prices moving within a range instead of drifting. *Prices that move within a range are a working market; prices that drift are a broken one.*

---

# 🏘 The three-town economy (draft)

*Draft from 18 Sep. The numbers get redone at step 3c. Towns now sit on the [world map](#-the-world), so what they can make comes from the land in their work area, not a terrain label. Fishing (step 7) will also give Hillfort some food of its own.*

The rule that makes it work: **tools wear out.** Farming, hunting and chopping all use them up, which gives Hillfort a customer every tick. If tools lasted forever, it would sell a few and then starve.

| Town | Terrain | Makes | Its food | Buys |
|---|---|---|---|---|
| **Farmstead** | Grassland | Grain | Grain, big surplus | Tools, firewood |
| **Woodhaven** | Forest | Wood; meat by hunting | Meat, feeds itself | Tools |
| **Hillfort** | Hills | Tools | None | Grain or meat, wood |

**Units:** 100 people per town. Each person does **1 work** per tick, eats **1 food** and burns **0.1 wood** as firewood.

**Recipes** ("0.1 tool" means a tool lasts 10 uses):

| Makes | Takes | Where |
|---|---|---|
| 3 grain | 1 work + 0.1 tool | Grassland |
| 2 meat | 1 work + 0.1 tool | Forest |
| 2 wood | 1 work + 0.1 tool | Forest |
| 1 tool | 4 work + 1 wood | Hills |

**Does it balance?** Per tick, if Hillfort eats grain:

| | Work used | Makes | Sells |
|---|---|---|---|
| Farmstead | 67 of 100 | 200 grain | 100 grain |
| Woodhaven | 72 of 100 | 100 meat, 44 wood | 34 wood |
| Hillfort | 55 of 100 | 14 tools | 14 tools |

The world eats 300 food and could make up to about 500. Every town both buys and sells, so money can circulate.

**One to watch: Woodhaven.** Meat costs more work per food than grain does, so Woodhaven may spend a bit more than it earns. It might start buying cheap grain instead of hunting, or tool prices might shift. That's the sim's job to find out.

**Defaults picked (easy to change):**
- Hillfort has no food. Fish and rivers can come later with the map.
- No separate iron ore. Mining is folded into the tool recipe, so there are four goods.
- Firewood is a second need, so Woodhaven always has customers.

---

# 🗺 Roadmap

| # | Step | Status |
|---|---|---|
| 1 | Pick the language | ✅ TypeScript |
| 2 | Three-town economy design | ✅ draft (numbers redone at 3c) |
| — | World design | ✅ confirmed 19 Sep |
| 3a | **World formula:** height, lake, hills, forest, sea, the two rivers, plus a map viewer page | ▶ designing the maths |
| 3b | **Towns** as patches of 1-hectare town and field tiles, with work areas | |
| 3c | **Produce and eat.** No prices, no trade | |
| 4 | Prices, with recipe inputs and firewood counting as demand | |
| 5 | Trade between towns (straight-line travel time), money conserved. Aim: the success test above | |
| 6 | **Caravans:** you write A*, one trader cart, routes remembered | |
| 7 | **Fishing**, then **boats** | |
| 8+ | Routes become roads · towns grow and claim land · rain and emergent rivers · terracing · mines in the hills by Hillfort · floating logs down rivers · sea trade with the outside world · zoomed-in settlement view · the game | later |

**No game graphics, multiplayer or Telegram until three towns run 1,000 ticks without dying.** The map viewer from step 3a is a tool for checking the world, not the game.

---

# 🐍 The Python prototype (reference)

**Frozen at:** tag `python-prototype` (commit `9f031a7`). See it on GitHub via the branch dropdown → **Tags**, or locally with `git checkout python-prototype` (`git checkout main` to come back).

**Run it:**

```bash
python ui_main.py                                  # window
python ui_main.py --headless --ticks 500           # text only
```

**What's built:**

| Feature | |
|---|---|
| Settlements with population, terrain, wealth, labour, storage, 3D coordinates | ✅ |
| Goods and recipes defined in `config.json` / `recipes.json` | ✅ |
| Recipe-based production; population-driven eating with hunger | ✅ |
| Local prices from supply and demand | ✅ (demand only for food) |
| Trade on price gaps, with transport cost and travel time | ✅ |
| Conserved money (`transfer_wealth`, per-tick check) | ✅ PR #1 |
| Abandonment (starvation) and migration | ✅ (wealth triggers can't fire any more) |
| Market upgrades | ✅ (need 200+ people) |
| Tkinter window: map with moving shipments, detail panels, trade analysis | ✅ |
| Headless mode | ✅ PR #2 |

**How it works:** [`notes/`](notes/README.md).

---

# 🎮 The bigger picture

### Trader agents: the long-term answer to trade

The old design documents already preferred **trader agents** ("Model B") over abstract town-to-town trade. They're also self-limiting. If trade needs a cart, and a cart takes six ticks to cross the map carrying forty units, then the number of trades is capped by the number of carts, not by a config value. **Start with one trader**: one cart, visible as a moving block, and you can watch a single decision and understand why it happened. A trader has a position, a cargo hold, its own money, and must decide where to go next. **That decision is the game.**

### The game: "The Gilded Road"

The merchant tycoon concept. Each player is a trader inside an economy they don't control.

| | |
|---|---|
| Simulation first, game second | ✅ the right order |
| Slow multiplayer, a week or more per game | Unusual and appealing. The world runs whether or not you log in |
| Adjustable tick speed | Comes free with a headless loop |
| Runs on your PC or a server | A Node process |
| Telegram or web | Telegram suits a check-in-once-a-day rhythm |
| Pixel graphics, traders as coloured blocks | A moving block is easier to read than a sprite |

⭐ **Open question, worth answering before building the game:** do players **compete for the same goods**, or run **separate routes**? If they compete, the economy is the opponent and there's drama. If not, it's a shared screensaver.

### Why TypeScript

| You want | TypeScript gives |
|---|---|
| Runs on a PC or server | Node, headless, same code |
| Telegram bot | `node-telegram-bot-api`, a few dozen lines |
| A website | Same language, same data structures |
| Friends playing over days | A Node process holding state, a web page reading it |
| Simple pixel map | HTML canvas |
| Maybe Android later | Wrap the web app |

The types also catch the kind of bug that's hard to spot in Python (a missing field, a misspelled key). C# was the alternative: more enjoyable to write, and the route to Unity.

### The approach

Small, and understood. A new, tiny core that grows one piece at a time, with every line understood. The Python repo is for reference: read it when stuck, don't port it.

---

# 📚 Design documents

| Where | What |
|---|---|
| **Obsidian** → `Simulation - Trade System Prototype.md` | ⭐ Main design doc: world → civilization → region → settlement hierarchy, bulk vs item tracking, Model A (abstract flow) vs **Model B (trader agents)**, market levels, hubs |
| Obsidian → `Trade Simulation - Development Hub.md` | Index of every sub-design |
| Obsidian → `Simulation - Feasibility.md` | The bigger dream: from caves to caravans |
| Obsidian → `Simulation - Testbed.md` | Plan for simplified test worlds |
| Drive → `Simulation Engine Choice Analysis` | Report on engine options (C#, Dwarf Fortress / Skyrim scale) |
| Drive → `Game Simulation Ideas Summary` | Three game concepts; **"The Gilded Road"** chosen |
| Drive → `03 Reference/TRADE-SIM-2026-09-18.md` | The original project file this one replaces |

⚠ **Housekeeping:** the Obsidian vault exists in four duplicate copies on Drive, and `Simulation - Trade System Prototype.md` appears at least twice with different lengths. Pick the real one before relying on it.

---

# 🧰 Git cheat sheet

| Command | What it does |
|---|---|
| `git pull` | Download the latest from GitHub and update your files |
| `git status` | What's changed and not yet committed |
| `git log --oneline -5` | The last 5 commits |
| `git checkout python-prototype` | Look at the frozen Python version (`git checkout main` to return) |
| `git fetch --tags --force` | Update your tags if one was moved on GitHub |

**How a change gets in:** new branch → commit → push → pull request on GitHub → you review **Files changed** → **Merge pull request** → **Delete branch** → `git pull` in your folder.

**Never** paste a token or password into chat. Sign in with `gh auth login` → **Login with a web browser**.

---

# 📓 Session log

### 19 September 2026
- Decided settlements should sit on a real map, with terrain belonging to the world.
- **Confirmed the world design**: 200 × 200 km formula world, central lake, eastern hills, north-western forest, sea to the south, one river into the lake and one out to the sea.
- Settlements become patches of 1-hectare tiles with work areas. Caravans plan with A* on a 1 km grid and remember routes. Fishing and boats come at step 7.
- Started the world formula. **Layer 1 settled**: hills moved to the north, one straight river along x = 0, lake about a day's walk across, north edge about 840 m.
- Next: Layer 2, noise.

### 18 September 2026
- Measured the wealth drain: transport 55%, upkeep 34%, tool fee 11%. **Made money a conserved currency** (PR #1).
- Found the real killer is food: ~20 made per tick vs ~50 eaten. Found money then pools with the food seller.
- Decided on TypeScript and a three-town restart; drafted the three-town design.
- Set up the GitHub CLI; first pull requests.
- **Rescued the April 2025 headless mode** from uncommitted changes (PR #2).
- Tagged the finished Python version as `python-prototype`.
- Wrote the [`notes/`](notes/README.md) on every Python file, and this project file (PR #3).

---

# ✏ Keeping this file current

At the end of each session:
1. Update **Last updated** and the **NOW** section (focus, where things stand, next steps).
2. Add any new **decisions**.
3. Add a **session log** entry.
4. Tick off **roadmap** steps.
