# Project file

*Last updated: 20 November 2026 · **Restarted** on this date*

**Read this first when you come back.** The top section says what we're doing and what's next. The game itself is described in [`docs/VISION.md`](docs/VISION.md). Updated at the end of every session.

---

# 📍 NOW

**Phase: Stage 0, planning the restart.** No code yet. We're deciding what the game is, how it's built and in what order, so every later step has a place in the plan.

**Where things stand:**
- **The game is defined:** a fantasy medieval world where you play a wandering trader who works their way up. See [`docs/VISION.md`](docs/VISION.md).
- **The language is chosen: C# / .NET.** Claude writes the code; you understand every piece through design notes before it's built.
- The September work (Python prototype, 200 km lake world, TypeScript plan) is in [`archive/`](archive/). The noise maths in [`notes/world-formula.md`](notes/world-formula.md) carries over.

## Next steps

| # | Step | Who | Status |
|---|---|---|---|
| 1 | Read [`docs/VISION.md`](docs/VISION.md) and correct anything that's wrong or missing | You | any time |
| 2 | Install the free **.NET SDK** | Claude | ✅ .NET 10 (long-term support) installed 20 Nov |
| 3 | **[Design note 1.0: how the world is made](docs/design/1.0-how-the-world-is-made.md).** The whole world-generation pipeline on one page: height → temperature → rain → rivers → fertility → biomes, the world's size, units and the size of the test region. Draft written; answer its questions in section 10 | Together | ▶ now |
| 4 | **Design note 1.1: height.** Finish the noise lessons (2D value noise, octaves, simplex), then shape a landmass with ocean around it | Together | after 3 |
| 5 | Build 1.0 + 1.1 in C#, with a first map picture | Claude, after you understand the notes | after 4 |

## Resume quickly

1. In `C:\Projects\trade-system-prototype`, run `git pull`.
2. Read **NOW** above, then the newest design note in [`docs/design/`](docs/design/) (empty until note 1.0 is written).
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

Each stage ends with something you can run and look at. Early stages are deliberately simple; realism is added stage by stage.

| Stage | What | You'll be able to |
|---|---|---|
| **0** | **Restart and plan:** vision, roadmap, language, way of working | Read the plan ▶ *now* |
| **1** | **The world**, built and checked on a small test region first: | See the world as a pixel map, zoom around it |
| | 1.1 height (noise, mountains, coasts, ocean all round) | |
| | 1.2 temperature (north–south and altitude) | |
| | 1.3 rain (wind, moisture, rain shadows) | |
| | 1.4 rivers and lakes (water flowing downhill) | |
| | 1.5 fertility and biomes | |
| | 1.6 map viewer | |
| **2** | **Where people live:** settlements placed by the land (water, fertility, coasts), species and cultures (e.g. dwarves in the mountains), what each place can make | See hundreds of settlements that make sense where they are |
| **3** | **Produce and eat:** goods, recipes, food, the food maths. No trade yet | Watch each settlement feed itself, or fail to |
| **4** | **Markets and money:** local prices from supply and demand, conserved money, barter where there's no coin | See prices differ from region to region |
| **5** | **AI traders and routes:** traders that find their way (A*), carry goods, remember routes; paths becoming roads | Watch caravans move and roads appear |
| **6** | **The player:** a trader on foot, buying and selling, travel time, solving the **time-scale** problem | Play the first loop: buy low, walk, sell high |
| **7** | **Growing up:** horse, cart, caravan, hired traders, a company | Feel the progression |
| **8** | **A world that reacts:** weather events, bad harvests, settlements growing and shrinking, your choices rippling out | See the world change because of you |
| **9** | **Settle down:** property, influence, local government | Play the late game |
| **10** | **Looks:** proper pixel-art top-down view, zooming into towns | Have something that looks like a game |
| Later | Scale up to a Japan-sized country, more species, the sea and foreign ports, multiplayer? | |

**The success test for stages 3–5** (carried over from the Python prototype): years of game time, nobody starves, money stays constant, and prices move within a range rather than drifting away.

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

### Before the restart
See [`archive/2026-09-plan/PROJECT-2026-09.md`](archive/2026-09-plan/PROJECT-2026-09.md#-session-log) (18–19 September 2026: Python fixes, three-town design, the 200 km world, the first noise lessons).

---

# ✏ Keeping this file current

At the end of each session: update **Last updated**, **NOW**, new **decisions**, the **session log**, and tick the **roadmap**. Then update the **Latest update** box in [`README.md`](README.md).

**Git in one line:** new branch → commit → push → pull request → you review **Files changed** → **Merge** → `git pull` in your folder.
