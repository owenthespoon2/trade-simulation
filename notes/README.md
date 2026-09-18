# Notes

## The new world

| Note | What it is |
|---|---|
| [world-formula.md](world-formula.md) | ⭐ The maths behind the world, layer by layer, as we learn it. Ends with **where we stopped** |

## The Python prototype

These notes explain how the Python prototype works, one file at a time. They're written for learning: to understand the code well enough to rebuild the important parts in TypeScript yourself.

The Python code is frozen at the git tag `python-prototype`. For what we're working on now, see [`PROJECT.md`](../PROJECT.md).

### Reading order

| # | Note | File(s) | What it is |
|---|---|---|---|
| 1 | [trade_logic.md](trade_logic.md) | `trade_logic.py` | ⭐ The simulation engine. Read this one properly |
| 2 | [world_setup.md](world_setup.md) | `world_setup.py` | Builds the starting world from the data files |
| 3 | [config_and_recipes.md](config_and_recipes.md) | `config.json`, `recipes.json` | Every number and recipe, and which ones matter |
| 4 | [ui.md](ui.md) | `ui_main.py` + 4 `ui_*.py` files | The window, the map, and headless mode |

Tip: keep the headless mode running in a terminal while you read, so you can see each part in action:

```bash
python ui_main.py --headless --ticks 200 --print_interval 20
```

### How the files fit together

```
ui_main.py            ← you run this
   │
   ├─ world_setup.py  ← reads config.json + recipes.json,
   │                    builds a World with goods, recipes and 5 settlements
   │
   └─ then, forever:  world.simulation_step()   ← trade_logic.py, one tick
                      then draw or print the result
```

The key idea: **`trade_logic.py` knows nothing about windows or printing.** It only holds the world and advances it one tick at a time. Everything else just builds the world or displays it. That separation is the most valuable thing to carry into TypeScript.

### Words used in the notes

| Word | Meaning |
|---|---|
| **Tick** | One step of simulated time. Everything (produce, eat, trade) happens once per tick |
| **Settlement** | A town: population, terrain, a store of goods, and wealth |
| **Good** | A type of thing: wood, grain, bread, tools… |
| **Bulk good** | Tracked only as a quantity ("40 grain"). Most goods |
| **Item good** | Tracked as individual objects with a history (`ItemInstance`). Only tools |
| **Recipe** | How to make a good: inputs + labour → outputs, maybe only on certain terrain |
| **Labour pool** | How much work a settlement can do per tick (population × 0.5) |
| **Local price** | What a good costs in one settlement, from its own supply and demand |
| **Shipment** | Goods travelling between settlements after a trade |
| **Money supply** | Total wealth in the world. Fixed after setup: money only moves |
