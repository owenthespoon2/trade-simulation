# `trade_logic.py`: the simulation engine

**What it is:** the whole simulation, about 930 lines. It defines what a settlement is, how goods are made, eaten, priced and traded, and what happens in one tick. It never draws or prints a summary. Other files call it.

**If you only remember one thing:** the simulation is a loop that calls `World.simulation_step()` over and over. Each call runs the same phases in the same order. Understanding that order is understanding the simulation.

---

## 1. The pieces

| Name | Kind | What it is |
|---|---|---|
| `Good` | class | A type of good: name, base value, colour, type (FOOD, RAW_MATERIAL, TOOL), and its recipe if it can be made |
| `ItemInstance` | class | One individual item (only tools) with an origin and trade history. Groundwork for "provenance", not really used yet |
| `transfer_wealth()` | function | The only way money moves. Takes from one holder, gives to another, refuses to overdraw |
| `Settlement` | class | A town. Holds its own stock, wealth and prices, and knows how to produce, consume and price |
| `Region`, `Civilization` | classes | Groupings of settlements. They exist but do nothing |
| `World` | class | Holds everything, finds and executes trades, moves shipments, and runs the tick |

Everything important lives in `Settlement` and `World`.

---

## 2. One tick, in order

This is `World.simulation_step()`, top to bottom. Each settlement does each phase before anyone moves to the next phase.

| # | Phase | What happens | Code |
|---|---|---|---|
| 1 | Reset | Tick counter +1, clear per-tick counters and logs | start of `simulation_step` |
| 2 | Shipments arrive | Any shipment whose arrival tick has come is added to the buyer's storage | "Shipment Arrival Phase" |
| 3 | Construction | Market upgrades in progress pay their cost and complete | `Settlement.progress_upgrade` |
| 4 | **Produce** | Each settlement turns labour and inputs into goods | `Settlement.produce` |
| 5 | **Consume** | Each population eats | `Settlement.consume` |
| 6 | **Prices** | Each settlement recalculates its local prices | `Settlement.update_prices` |
| 7 | **Find trades** | Compare every pair of settlements for every good | `World.find_trade_opportunities` |
| 8 | **Execute trades** | Carry out the best ones: pay, remove goods, send a shipment | `World.execute_trades` |
| 9 | Upgrade decisions | Busy settlements decide whether to build a bigger market | `Settlement.decide_upgrade` |
| 10 | Abandonment | Starving (or very poor) settlements are abandoned; people and money move | "Abandonment Check Phase" |
| 11 | Migration | Every 5 ticks, poor settlements lose people to rich ones | "Regular Migration Phase" |
| 12 | Money check | Warn if total wealth ≠ money supply | "Money Conservation Check" |

**Order matters.** For example, prices (6) are set *after* eating (5), so a settlement that just ate its bread sees a high bread price and becomes a buyer in the same tick.

---

## 3. Settlements

### What a settlement holds

| Field | Meaning |
|---|---|
| `population`, `terrain_type`, `x, y, z` | Who and where |
| `bulk_storage` | Dictionary: good → quantity, e.g. `{"grain": 120.5}` |
| `item_storage` | Dictionary: good → list of `ItemInstance` (tools) |
| `wealth` | Money |
| `local_prices` | Dictionary: good → price here, this tick |
| `consumption_needs` | Dictionary: good → hunger multiplier, starting at 1.0 |
| `max_labor_pool` | population × 0.5, the work available per tick |
| `storage_capacity` | population × 10 (×1.5 once population ≥ 150, a "city") |
| `market_level`, `trade_capacity` | How many trades per tick it can do (5, or 15 at level 2) |

`update_derived_stats()` recalculates labour and storage whenever population changes.

### Storage: `add_to_storage` / `remove_from_storage`

- **Adding** is limited by free space and returns how much actually fitted. Anything that doesn't fit is lost.
- **Removing** takes from bulk stock first, then from item instances, and returns how much it actually got.

Both return the real amount because callers can't assume they got what they asked for.

### Producing: `produce()`

1. Refill the labour pool to its maximum.
2. Do up to **5 passes** (`max_production_passes`). In each pass, visit every producible good in random order and make **one batch** if:
   - the terrain is allowed (e.g. grain only on Grassland or Plains),
   - there's enough labour left,
   - the inputs are in storage.
3. Take the labour and inputs, add the outputs. If the outputs don't fit in storage, undo everything for that batch.

⚠ **This is the hidden food cap.** Each recipe runs at most 5 times per tick. A 100-person farm has 50 labour, and grain costs 5 labour per batch, so it makes at most 5 grain and leaves the rest of its labour idle.

### Eating: `consume()`

1. **Bread first.** Need = 0.1 × population × bread hunger multiplier × a random ±10%. With 100 people and no hunger, that's about 10 bread.
2. **Grain covers the rest**, multiplied again by the grain hunger multiplier.
3. **Hunger multipliers adjust.** If less than 90% of a need was met, that multiplier goes ×1.1 (max 3.0). If it was met, ×0.95 (min 1.0).
4. **Starvation counter.** If less than half the food need was met, `ticks_below_food_threshold` goes up by one; otherwise it resets to 0. At 20 the settlement is abandoned.

⚠ **Hungry people eat *more*.** The multiplier changes actual eating, not just prices. A starving town can try to eat 3× its normal bread, and grain can reach 9× (both multipliers stacked). That makes collapses happen faster.

### Pricing: `update_prices()`

For every good:

```
supply = stock here (at least 0.01)
demand = 0.1 × population × hunger multiplier   ← only for bread and grain
       = 0.01                                    ← every other good
price  = base_value × (supply / demand) ^ (−price_sensitivity)
then clamp between 0.1× and 10× base_value
```

With `price_sensitivity` = 0.5, worked examples:

| Good | Stock | Demand | Price |
|---|---|---|---|
| Bread (base 12) | 500 | 10 | 12 × (50)^−0.5 = **1.70**, lots of bread so it's cheap |
| Bread (base 12) | 5 | 10 | 12 × (0.5)^−0.5 = **16.97**, scarce so it's expensive |
| Wood (base 5) | 30 | 0.01 | 5 × (3000)^−0.5 = 0.09, clamped up to **0.50** |
| Wood (base 5) | 0 | 0.01 | 5 × (1)^−0.5 = **5.00** |

⚠ **Only food has demand.** Any stock of wood, iron, seed or tools drives its price to the floor, because the demand is a token 0.01. So non-food producers can barely earn anything, and money flows one way, to whoever sells food. We measured this: with food fixed, all 5,000 wealth ends up in the grain town. The fix is for recipe inputs to count as demand too.

⚠ The good IDs `'bread'`, `'grain'`, `'iron_ore'` and `'seed'` are written directly into `consume()` and `update_prices()`. Adding a new food in `config.json` wouldn't make anyone eat it.

### Market upgrades: `decide_upgrade()` / `progress_upgrade()`

When a settlement has been blocked by its trade capacity 5 times, it tries to build Market level 2, which costs 50 wood, 5 tools and 100 labour and gives +10 trades per tick.

⚠ A 100-person town only has 50 labour, so it can never afford the 100 labour. Only towns grown by migration (200+ people) ever upgrade.

---

## 4. The World

### Finding trades: `find_trade_opportunities()`

For **every pair** of active settlements and **every good**:

```
transport cost per unit = distance × 0.0005
if the price gap between the two is bigger than the transport cost:
    the cheaper settlement is the seller, the dearer one the buyer
```

The list is sorted by price gap, biggest first. With 5 settlements and 6 goods that's 10 pairs × 6 goods = 60 checks per tick, which is where the "hundreds of trades" came from.

### Doing trades: `execute_trades()`

Going down the sorted list, each trade:

1. Is skipped if the world has done 200 trades this tick, or either settlement has used up its trade capacity.
2. **Quantity** = the smallest of: the seller's *entire* stock, what the buyer can afford, and the buyer's free storage. Then it's capped so the cost is at most 25% of the buyer's wealth.
3. **Payment:** the buyer pays `(seller's price + transport) × quantity` to the seller, through `transfer_wealth()`.
4. **Goods** leave the seller now and go into a **shipment** arriving `ceil(distance ÷ 50)` ticks later.

Worked example: Farmstead (100, 100, 0) and Metropolis (250, 200, 0) are 180 apart. Transport is 180 × 0.0005 = 0.09 per unit, and the trip takes ceil(180 ÷ 50) = 4 ticks. Grain costs 3.00 at Farmstead and 9.00 at Metropolis, so the gap of 6.00 beats 0.09 and a trade happens. Metropolis has 1,000 wealth, so it spends at most 250, which buys 250 ÷ 3.09 ≈ 81 grain. Farmstead receives 250 and the grain arrives on tick +4.

⚠ **Sellers sell everything.** The quantity starts from the seller's whole stock, including food it needs to eat. The buyer's price only decides whether to trade; it's never paid.

### Shipments

Each shipment is a dictionary: who, what, how much, departure tick and arrival tick, and real-world seconds for the map animation. They wait in `world.in_transit_shipments` until their arrival tick.

⚠ If the buyer's storage is full, or the buyer was abandoned, the goods are lost, even though the buyer already paid.

### Abandonment and migration

- **Abandonment:** 20 ticks of starvation, or 15 ticks below −100 wealth. The whole population *and its wealth* move to the nearest active settlement (`_handle_final_migration`).
- **Migration:** every 5 ticks, settlements below 0 wealth send 10% of their people to the nearest settlement with at least 600 wealth.

⚠ Wealth can't go negative any more (see below), so the −100 and 0 triggers never fire. Only starvation abandons a town, and economic migration never happens.

### Money

Money is a **conserved currency**: it's never created or destroyed after setup, only moved.

- `World.money_supply` is the total of every settlement's starting wealth, added up in `add_settlement()`.
- Every payment goes through `transfer_wealth(payer, payee, amount)`, which raises an error rather than let a balance go negative.
- At the end of every tick, if `get_total_wealth()` differs from `money_supply`, it prints `WARN ... Money not conserved!`.

Before this change (PR #1), transport costs, storage upkeep and a tool-making fee deleted money every tick, and the world ran out by tick ~100.

---

## 5. Known problems (summary)

| Problem | Where | Effect |
|---|---|---|
| Recipe runs capped at 5 per tick; grain barely feeds the farmer | `produce`, recipes | World makes ~20 food per tick and eats ~50. **Everyone starves by tick ~100** |
| Hunger multiplies actual eating | `consume` | Collapses speed up |
| Only bread and grain have price demand | `update_prices` | Non-food sells at the floor; money pools with the food seller |
| Sellers sell their entire stock | `execute_trades` | The farm can sell away its own food |
| Wealth thresholds can't be reached | abandonment, migration | Poverty never triggers anything |
| Goods lost on arrival, already paid for | shipment arrival | Buyer loses money for nothing |
| Upgrade needs more labour than a town has | `building_definitions` | Upgrades only after migration |
| Good IDs hard-coded | `consume`, `update_prices` | New goods in config don't behave like food |
| Every pair × every good checked every tick | `find_trade_opportunities` | Trade spam, capped only by config numbers |

---

## 6. For the TypeScript version

**Carry over:**
- The tick loop with a fixed phase order.
- `transfer_wealth()` and the money-supply check, from day one.
- Recipes as data: inputs, outputs, labour, allowed terrain.
- Storage as a simple map: good → quantity.
- Prices from supply and demand, clamped to a range, **but** with demand counting everything that's eaten, burned or used as a recipe input.
- The engine never drawing or printing anything itself.

**Leave behind (for now):**
- Production passes. Let labour be the limit.
- Hunger multipliers that change how much people eat.
- `ItemInstance`, market levels, regions, civilizations, migration, abandonment. Add each back one at a time, later.
- Hard-coded good names. Use a good's type (FOOD, FUEL, TOOL) instead.
- Direct settlement-to-settlement trade, eventually. **Trader agents** replace it, which limits trade naturally: one cart can only be in one place.
