# `config.json` and `recipes.json`: the numbers

**What they are:** all the tunable numbers, kept out of the code so you can change the simulation without editing Python. `world_setup.py` reads both at startup.

- `config.json` has four sections: `simulation_parameters`, `ui_parameters`, `goods_definitions` and `building_definitions`.
- `recipes.json` says how each good is made.

**Status key:** ✅ used · ⚠ never read by the code · 🚫 can't trigger any more (wealth can't go negative since PR #1)

---

## Goods (`goods_definitions`)

| ID | Base value | Type | Tracked as |
|---|---|---|---|
| wood | 5 | RAW_MATERIAL | bulk |
| iron_ore | 10 | RAW_MATERIAL | bulk |
| seed | 2 | RAW_MATERIAL | bulk |
| grain | 8 | RAW_MATERIAL | bulk |
| tools | 50 | TOOL | items (`ItemInstance`) |
| bread | 12 | FOOD | bulk |

**Base value** is the "normal" price. Local prices move between 0.1× and 10× it depending on supply and demand. Grain is typed RAW_MATERIAL, but the code eats it anyway, because `'grain'` is written directly into `consume()`.

## Recipes (`recipes.json`)

| Good | Inputs | Labour | Output | Terrain | Output per labour |
|---|---|---|---|---|---|
| wood | 0.05 tools | 3 | 1 wood | Forest, Hills | 0.33 |
| iron_ore | — | 5 | 0.5 ore | Mountain, Hills | 0.10 |
| seed | — | 2 | 0.5 seed | Grassland, Hills | 0.25 |
| grain | 0.1 seed | 5 | 1 grain | Grassland, Plains | 0.20 |
| tools | 2 ore + 0.5 wood | 10 | 1 tool | anywhere | 0.10 |
| bread | 1 grain + 0.1 wood | 1 | 2 bread | anywhere | (doubles grain) |

**A chicken-and-egg problem:** wood needs tools, and tools need wood. At the start nobody has tools, and only Craftburg has both wood and ore, enough for about 2 tools. The whole wood and tools chain grows out of that tiny seed stock.

### The food maths: why everyone starves

- A person gives **0.5 labour** per tick and eats **0.1 food** per tick.
- Grain takes 5 labour, so one person's work grows 0.1 grain: **exactly what they eat, with nothing to spare.**
- Turning grain into bread doubles it, so a farmer who bakes feeds about 1.5 people.
- The world needs 5 towns × 10 = **50 food per tick**, but only 2 towns can farm.
- On top of that, `max_production_passes: 5` caps each recipe at 5 batches per tick. That's 5 grain per farm, 10 in total, or at most 20 bread.

**Result: about 20 food made per tick against 50 eaten.** The 3,100 starting food runs out around tick 100.

**Lesson for TypeScript:** before coding, check on paper that food made ≥ food eaten, with some slack.

---

## Simulation parameters

### Prices

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `price_sensitivity` | 0.5 | How strongly price reacts to supply ÷ demand. Higher means wilder swings | ✅ |
| `min_price_multiplier` | 0.1 | Price floor = 0.1 × base value | ✅ |
| `max_price_multiplier` | 10.0 | Price ceiling = 10 × base value | ✅ |
| `trade_profit_margin_threshold` | 1.05 | Probably meant "only trade if at least 5% profit" | ⚠ never read |

### Population, work and storage

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `labor_per_pop` | 0.5 | Labour per person per tick | ✅ |
| `max_production_passes` | 5 | Max batches of each recipe per tick. **The hidden food cap** | ✅ |
| `storage_capacity_per_pop` | 10 | Storage space per person | ✅ |
| `city_population_threshold` | 150 | Population at which a town counts as a city (bigger storage, red on the map) | ✅ |
| `city_storage_multiplier` | 1.5 | Storage bonus for cities | ✅ |
| `settlement_default_initial_wealth` | 1000 | Starting money per town (so 5,000 in the world) | ✅ |

### Eating and hunger

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `base_consumption_rate` | 0.1 | Food eaten per person per tick | ✅ |
| `consumption_fulfillment_threshold` | 0.9 | Getting less than 90% of a need counts as "short" | ✅ |
| `consumption_need_increase_factor` | 1.1 | Hunger multiplier ×1.1 each short tick | ✅ |
| `consumption_need_decrease_factor` | 0.95 | …and ×0.95 each satisfied tick | ✅ |
| `consumption_need_max_multiplier` | 3.0 | Hunger multiplier cap. It raises *actual eating* too, which is a problem | ✅ |

### Trade and transport

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `transport_cost_per_distance_unit` | 0.0005 | Cost per unit of goods per unit of distance (≈0.1 for a typical trip). Paid to the seller | ✅ |
| `base_transport_speed` | 50 | Distance per tick. Trips between the five towns take 4–8 ticks | ✅ |
| `max_trade_cost_wealth_percentage` | 0.25 | One trade can cost at most 25% of the buyer's wealth | ✅ |
| `min_trade_qty` | 0.01 | Smallest trade allowed | ✅ |
| `max_trades_per_tick` | 200 | World-wide limit on trades per tick | ✅ |
| `base_trade_capacity` | 5 | Trades per settlement per tick at market level 1 | ✅ |
| `market_upgrade_fail_trigger` | 5 | Times blocked by capacity before trying to upgrade the market | ✅ |

### Abandonment and migration

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `food_abandonment_threshold` | 0.5 | Getting under 50% of food counts as a starving tick | ✅ |
| `food_abandonment_ticks` | 20 | Starving ticks in a row before abandonment | ✅ |
| `abandonment_wealth_threshold` | −100 | Wealth below this counts as a poor tick | 🚫 |
| `abandonment_ticks_threshold` | 15 | Poor ticks in a row before abandonment | 🚫 |
| `migration_check_interval` | 5 | Check migration every 5 ticks | ✅ |
| `migration_wealth_threshold` | 0 | Towns below this lose people | 🚫 |
| `migration_target_min_wealth` | 600 | Towns at or above this attract people | ✅ (but nobody leaves) |
| `migration_max_percentage` | 0.1 | Share of people who leave per check | 🚫 |

### Logs

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `settlement_log_max_length` | 10 | Events kept per settlement for the UI | ✅ |
| `world_trade_log_max_length` | 10 | Recent trades kept for the UI | ✅ |

## Buildings (`building_definitions`)

Only the market. Level 1 is free and gives 5 trades per tick. Level 2 costs **50 wood, 5 tools and 100 labour** and adds +10 trades per tick. A 100-person town has only 50 labour, so it can't build level 2 until it has grown to 200+ people.

## UI parameters

These only affect the window, never the simulation.

| Parameter | Value | Meaning | Status |
|---|---|---|---|
| `tick_delay_ms` | 1000 | Real-time milliseconds per tick in the window | ✅ |
| `animation_frame_delay_ms` | 33 | Map redraw interval (~30 frames per second) | ✅ |
| `window_title` | … | Window title | ✅ |
| `settlement_base_radius`, `settlement_wealth_sqrt_scale`, `settlement_max_radius_increase` | 2, 0.5, 50 | Circle size on the map = base + √wealth × scale, capped | ✅ |
| `city_color`, `default_shipment_color` | colours | Map colours | ✅ |
| `shipment_marker_radius`, `shipment_marker_offset` | 3, 4 | Size and spacing of moving shipment dots | ✅ |
| `trade_effect_duration_ms` | 1200 | Read, but never used for anything | ⚠ |
| `trade_marker_radius` | 4 | — | ⚠ never read |

---

## For the TypeScript version

**Carry over:**
- Numbers in data, not scattered through code.
- Recipes as a table: inputs, labour, outputs, terrain.

**Change:**
- **Far fewer knobs.** The three-town version needs perhaps ten numbers. Every setting is something to understand and balance.
- **Clear units.** For example, 1 person = 1 work and eats 1 food per tick, instead of 0.5 and 0.1.
- **Every good has a job** marked by its type (FOOD, FUEL, TOOL), and the code uses the type, not the name.
- **No setting that nothing reads.** If it's in the config, the code must use it.
