# `world_setup.py`: building the starting world

**What it is:** one function, `setup_world()`, about 230 lines. It reads the two data files and builds a ready-to-run `World`: goods, recipes, five settlements, their starting stock, and regions. It runs once, before the first tick.

**Why it's separate from `trade_logic.py`:** *building* a world and *running* a world are different jobs. The engine doesn't care where settlements came from, whether that's this hand-written list today or a map generator one day.

---

## What `setup_world()` does, step by step

1. **Load `config.json`**, split into four parts: simulation parameters, goods, buildings and UI parameters.
   - If the file is missing, it falls back to a list of defaults written into the code.
2. **Create the `World`** with the simulation parameters.
3. **Create each `Good`** from `goods_definitions`: name, base value, colour, bulk or item, producible or not, and type.
4. **Load `recipes.json`** and attach each recipe to its good with `good.add_recipe(**recipe_info)`.
5. **Create five settlements**, all identical except name, terrain and position: population 100, wealth 1,000.
6. **Add starting stock** (table below).
7. **Group into regions and a civilization.** Nothing uses these yet.

## The five settlements

| ID | Name | Terrain | Position (x, y, z) | Can make (from recipes) |
|---|---|---|---|---|
| A | Farmstead | Grassland | 100, 100, 0 | Seed, **grain** |
| B | Logger's Camp | Forest | 100, 300, 5 | Wood |
| C | Mine Town | Mountain | 400, 100, 20 | Iron ore |
| D | Craftburg | Hills | 400, 300, 10 | Wood, iron ore, seed |
| E | Metropolis | Plains | 250, 200, 0 | **Grain** (but not seed, so it must buy seed) |

Anyone can make **tools** (iron ore + wood) and **bread** (grain + wood) if they have the inputs.

Only A and E can grow food. That's two farms feeding five towns, which is part of why everyone starves.

## Starting stock

| Settlement | Stock |
|---|---|
| A Farmstead | 500 seed, 500 grain, 500 bread |
| B Logger's Camp | 30 wood, 500 bread |
| C Mine Town | 10 iron ore, 500 bread |
| D Craftburg | 10 wood, 5 iron ore, 500 bread |
| E Metropolis | 100 grain, 500 bread |

So the world starts with **2,500 bread + 600 grain ≈ 3,100 food** and **5,000 wealth**. Eating ~50 food per tick and making ~20 means that food lasts roughly 100 ticks, which matches when everything collapses.

## Things worth knowing

**`add_recipe(**recipe_info)` means the JSON keys must match the function's parameter names exactly.** `**` unpacks a dictionary into named arguments, so `{"labor": 5, "outputs": {...}}` becomes `add_recipe(labor=5, outputs={...})`. An extra or misspelled key in `recipes.json` makes that recipe fail. Because the call is wrapped in `try/except`, setup doesn't stop: it prints an `ERROR` line and carries on with a good that can never be produced. That's easy to miss, and it's why removing `wealth_cost` meant editing both `recipes.json` and `add_recipe`.

**⚠ The fallback defaults don't match `config.json`.** If `config.json` can't be found, the code uses its own list, where `price_sensitivity` is 2.0 (config: 0.5) and transport cost is 0.02 (config: 0.0005). A typo in the file name would quietly give you a very different simulation. It would be better to stop with an error.

**Starting stock is hard-coded by settlement ID** (`world.settlements['A']`). Changing the settlements means editing code, not data.

**You can run this file on its own:**

```bash
python world_setup.py
```

The block at the bottom (`if __name__ == "__main__":`) only runs when the file is started directly, not when another file imports it. Here it prints every good, settlement and region, which is a quick way to check the setup.

---

## For the TypeScript version

**Carry over:**
- Keep "build the world" separate from "run the world".
- Define the world as **data**: the three towns, their terrain, starting stock and recipes, all in one data file, so nothing about a specific town is written into the code.

**Change:**
- If the data is missing or wrong, stop with a clear error instead of silently carrying on. If the world data is a TypeScript file rather than JSON, the types catch this before it even runs: a recipe missing `labor` won't compile.
- Start with the three-town design in [`PROJECT.md`](../../../PROJECT.md): Farmstead, Woodhaven, Hillfort.
