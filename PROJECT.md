# Trade Simulation: project file

*Last updated: 18 September 2026*

**Read this first when you come back.** The top section says what we're doing and what's next. Everything below it is background. It gets updated at the end of every session.

---

# 📍 NOW

**Focus:** understand the Python prototype, then start the TypeScript rewrite with a tiny three-town version.

**Where things stand:**
- The Python prototype is **finished and frozen** at the git tag `python-prototype`.
- Money is now conserved, but settlements still starve around tick 100 (see [what we learned](#-what-the-python-prototype-taught-us)).
- Notes explaining every Python file are in [`notes/`](notes/README.md).

## Next steps

| # | Step | Who | Status |
|---|---|---|---|
| 1 | **Read the notes**, starting with [`trade_logic.md`](notes/trade_logic.md). Run headless mode alongside | You | ▶ next |
| 2 | **Confirm or tweak the [three-town design](#-the-three-town-world-draft)** | You | waiting |
| 3 | **Barebones TypeScript version** in a `ts/` folder: three towns produce and eat, one printed line per tick. No prices, no trade. About 100 lines. (Node.js v23 is already installed) | Claude writes, you read | after 1–2 |
| 4 | **Add prices** to it | You, with help | later |
| 5 | **Add trade** between towns | You, with help | later |

**Expected result of step 3:** without trade, Hillfort starves straight away (it has no food), and Farmstead and Woodhaven starve once their starting tools wear out. That shows every town needs trade.

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

# 🏘 The three-town world (draft)

*Not confirmed yet. Change anything.*

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
| 1 | Design the three-town world on paper | ✅ draft done, needs your OK |
| 2 | Pick the language | ✅ TypeScript |
| 3 | Towns produce and eat. No prices, no trade | next |
| 4 | Prices, with recipe inputs and firewood counting as demand | |
| 5 | Trade between towns, money conserved. Aim: the success test above | |
| 6 | **One trader cart** replaces direct trade | |
| 7 | Switch systems back on one at a time; then a map; then the game | |

**Nothing about graphics, multiplayer or Telegram until three towns run 1,000 ticks without dying.**

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
