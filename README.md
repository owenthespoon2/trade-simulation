# Trade Simulation

**A fantasy medieval world that runs by itself, and you, a wandering trader, trying to make your fortune in it.**

The land is shaped by maths: mountains, rivers, weather and biomes from frozen north to hot south. Civilisations farm, fish, mine and trade according to where they live. Dwarves in the mountains sell iron and mushrooms but can't grow grain. Farmers out in the fields have no coin and trade eggs for salt. You start alone and on foot, and work your way up to a horse, a cart, a caravan, a trading company, and maybe a seat in a city's government. Your choices ripple back into the world.

Inspired by Dwarf Fortress and RimWorld. Top-down and pixelated. Written in C#.

---

## 📢 Latest update: 20 November 2026, the restart

After a two-month break the project has **restarted** with a clearer idea of what it's for:

- **The game is defined:** a fantasy trader game in a living, simulated world. Full write-up in [`docs/VISION.md`](docs/VISION.md).
- **New language: C# / .NET.** It's fast enough for a big world with many people in it, and readable.
- **New way of working:** every system is written up as a design note with all its maths, understood, and only then built. The notes stay as the explanation of the code.
- **First up: the world.** Height, temperature, rain, rivers, fertility and biomes, on a small test region first.

**Now:** Stage 1, the world. [Design note 1.0](docs/design/1.0-how-the-world-is-made.md) (how the world is made) is agreed. **Next:** note 1.1, height. Details in [`PROJECT.md`](PROJECT.md#-now).

---

## The plan in one table

| Stage | What |
|---|---|
| 0 | Restart and plan ✅ |
| 1 | **The world:** height, climate, rivers, biomes, a pixel map ▶ *now* |
| 2 | Where people live: settlements, species, what each place makes |
| 3 | Produce and eat |
| 4 | Markets, prices, money and barter |
| 5 | AI traders, routes, roads that emerge |
| 6 | The player: a trader on foot |
| 7 | Horse, cart, caravan, company |
| 8 | A world that reacts: weather, harvests, your choices |
| 9 | Settle down: property and politics |
| 10 | Proper pixel-art looks |

## Ideas waiting their turn

- Paths that traders use become tracks, then paved roads.
- Bad weather in one region changes crop prices across the country.
- Barter in poor rural places; coin in towns and cities.
- Industries that follow the land: fishing on rivers, mining in mountains, tea and bamboo in the warm south.
- Two speeds of time: slow in town, fast on the road. Prices you saw last month may be stale when you arrive.
- Hire your own traders and run a company; settle down and get into local politics.
- A Japan-sized fantasy country with a few hundred cities and countless hamlets.

## Where to look

| | |
|---|---|
| [`PROJECT.md`](PROJECT.md) | ⭐ **Start here.** What we're doing now, next steps, roadmap, decisions |
| [`docs/VISION.md`](docs/VISION.md) | The full idea of the game |
| `docs/design/` | Design notes: the maths and logic of each system, written before it's built |
| [`notes/world-formula.md`](notes/world-formula.md) | Maths lessons so far (smoothstep, noise) |
| [`BOARD.md`](BOARD.md) | Small jobs queued for unattended AI runs |
| [`archive/`](archive/) | Earlier versions: the September 2026 plan and the original Python prototype |
