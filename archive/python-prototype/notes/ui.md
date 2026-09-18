# The UI files and headless mode

**What they are:** everything you can see: the Tkinter window, the map, the side panels, and the text-only headless mode. About 1,500 lines across five files.

**The important rule they follow:** the UI **only reads** the world. The one thing it ever does to the simulation is call `world.simulation_step()` once per tick. Everything else just looks at the settlements and draws or prints them. Because of that, the engine could be moved to TypeScript without the UI coming with it.

---

## `ui_main.py`: the entry point

This is the file you run. At the bottom, the `if __name__ == "__main__":` block reads the command-line options (with `argparse`) and picks a mode:

```bash
python ui_main.py                          # window
python ui_main.py --headless --ticks 500   # text only
```

### Window mode: the `SimulationUI` class

When created, it:
1. Builds the world with `setup_world()`.
2. Builds the window:
   - a control bar with **Start**, **Pause** and **Trade Analysis** buttons,
   - the static pane on the left,
   - two tabs on the right: **Settlement Details** and **Map**.
3. Starts **two separate loops**, using Tkinter's `root.after(delay, function)` ("call this function again in N milliseconds"):

| Loop | How often | What it does |
|---|---|---|
| `update_simulation` | once per tick (`tick_delay_ms`, 1 second) | Runs one `simulation_step()`, then refreshes every panel |
| `_update_animation_frame` | ~30 times a second | Only moves the shipment dots on the map |

Having two loops is why shipments glide smoothly even though the simulation only jumps once a second. The simulation starts paused.

### Headless mode: `run_headless_simulation()`

Written in April 2025, rescued in PR #2.

1. Build the world.
2. Loop: `simulation_step()`, and every `--print_interval` ticks, print a summary.
3. Stop at `--ticks`, or when every settlement has been abandoned.

The summary (`_print_headless_summary`) shows global totals, then each settlement in two side-by-side columns: population, wealth, labour, storage, inventory with local prices, production this tick, and elevated hunger. ANSI codes (e.g. `\033[93m`) colour the text in the terminal.

| Option | Does |
|---|---|
| `--ticks N` | Stop after N ticks (otherwise runs forever; Ctrl+C prints a final summary) |
| `--print_interval N` | Print a summary every N ticks (default 50) |
| `--mode continuous --delay S` | Wait S seconds between ticks and redraw the screen, like a live view |
| `--no-clear` | In continuous mode, don't clear the screen between summaries |
| `--config`, `--recipes` | Use different data files |
| `--output FILE` | ⚠ Accepted, but not implemented. It prints "(Not Implemented)" |

⚠ The summary's "Total Wealth" only counts *active* settlements, so it reads 0 once every town is abandoned. The money isn't lost. When a town is abandoned, its money moves with the migrants; when the very last town goes, the money stays in that empty town. The true total is `world.get_total_wealth()`.

---

## The four panel files

Each has a `setup_…` function that builds its widgets once, and an `update_…` function called every tick.

| File | Shows |
|---|---|
| `ui_static_pane.py` | Left column: **Settlements** list, **Goods** list (click one to see its **Recipe Details**), **Global Totals** of each good (including goods in transit), **Global Average Prices**, **Global Trade Volume** |
| `ui_dynamic_pane.py` | **Settlement Details** tab: a scrollable card per settlement with population, wealth, labour, storage, market level, trades this tick and in total, food and wealth warning counters, elevated hunger, inventory and production |
| `ui_map_pane.py` | **Map** tab: settlements as circles (size = base + √wealth × 0.5, capped; red when population ≥ 150), shipments as coloured dots moving between them, a goods colour legend, and the last trade's details |
| `ui_analysis_window.py` | **Trade Analysis** pop-up: tabs for executed trades, failed trades (with the reason), potential trades and migrations, with sortable columns |

### How the map animates shipments

Each shipment records its real-world departure and arrival time in seconds (`departure_time_sec`, `arrival_time_sec`). Every animation frame:

```
progress = (now − departure) ÷ (arrival − departure)     ← 0.0 to 1.0
position = start + (end − start) × progress
```

This is called linear interpolation. Dots travelling the same route are nudged sideways so they don't overlap (`_calculate_offset`). You'll want exactly the same trick for trader carts on a canvas map.

The map is 2D: it ignores the z coordinate.

---

## For the TypeScript version

**Carry over:**
- **Headless first.** Build the text output before any graphics, which is what your notes recommended. A printed summary every N ticks is enough to balance the three-town world.
- **The engine never draws; the display never changes the world.** In TypeScript that means the simulation in one module and printing or drawing in another.
- **Interpolated movement** for the map later, and a slower simulation clock separate from a fast drawing clock.
- The **Trade Analysis** idea: logging *why* a trade failed made the old simulation debuggable. Keep that habit.

**Leave behind:**
- Tkinter itself. A browser canvas replaces it later (step 7 of the roadmap).
- Most panels. Start with one printed table per tick, and only add views when you need to see something.
