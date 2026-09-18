import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import time # Keep time import
import traceback
import sys
import json
import random
import argparse
import os # Keep os import
import math # For ceiling division in columns

# --- Import Simulation Logic & Setup ---
try:
    from trade_logic import World, Good
    from world_setup import setup_world
except ImportError:
    print("ERROR: Make sure 'trade_logic.py' and 'world_setup.py' exist and are runnable.")
    sys.exit(1)

# --- Import UI Modules ---
# (Imports remain the same)
try:
    import ui_static_pane
    import ui_dynamic_pane
    import ui_map_pane
    import ui_analysis_window
except ImportError as e:
    print(f"ERROR: Failed to import UI module: {e}")
    print("Ensure ui_static_pane.py, ui_dynamic_pane.py, ui_map_pane.py, ui_analysis_window.py exist.")
    sys.exit(1)

# --- Import Theme ---
# (Theme import remains the same)
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    print("WARN: 'sv_ttk' library not found. UI will use default theme.")
    SV_TTK_AVAILABLE = False

# --- Load UI Configuration ---
# (Configuration loading remains the same)
DEFAULT_UI_PARAMS = {
    "tick_delay_ms": 1000, "animation_frame_delay_ms": 33, "trade_effect_duration_ms": 1200,
    "settlement_radius": 15, "trade_marker_radius": 4, "window_title": "Emergent Trade Simulation",
    "settlement_base_radius": 8, "settlement_wealth_sqrt_scale": 0.5, "settlement_max_radius_increase": 25,
    "city_color": "#e27a7a", "default_shipment_color": "#FFFFFF", "shipment_marker_radius": 3,
    "shipment_marker_offset": 4
}
DEFAULT_SIM_PARAMS = { "city_population_threshold": 150 }
ui_params = DEFAULT_UI_PARAMS.copy()
sim_params_for_ui = DEFAULT_SIM_PARAMS.copy()
def load_configuration(config_file="config.json"):
    global ui_params, sim_params_for_ui
    local_ui_params = DEFAULT_UI_PARAMS.copy(); local_sim_params_for_ui = DEFAULT_SIM_PARAMS.copy()
    full_sim_params = {}
    try:
        with open(config_file, 'r') as f: config_data = json.load(f)
        loaded_ui_params = config_data.get("ui_parameters", {}); full_sim_params = config_data.get("simulation_parameters", {})
        local_ui_params.update(loaded_ui_params); local_sim_params_for_ui['city_population_threshold'] = full_sim_params.get('city_population_threshold', DEFAULT_SIM_PARAMS['city_population_threshold'])
        print(f"Loaded parameters from {config_file}.")
    except FileNotFoundError: print(f"WARN: Config file '{config_file}' not found. Using default parameters.")
    except json.JSONDecodeError: print(f"ERROR: Could not decode {config_file}. Using default parameters.")
    except Exception as e: print(f"ERROR loading parameters from {config_file}: {e}. Using defaults.")
    ui_params = local_ui_params; sim_params_for_ui = local_sim_params_for_ui
    return full_sim_params

# --- ANSI Color Codes ---
# (Color codes remain the same)
C_RESET = '\033[0m'; C_BOLD = '\033[1m'; C_HEADER = '\033[96m'; C_SETTLEMENT = '\033[94m'
C_GOOD = '\033[92m'; C_VALUE = '\033[93m'; C_WARN = '\033[91m'; C_SUBTLE = '\033[90m'

# --- Theme colors ---
DARK_BG = "#2e2e2e"; DARK_FG = "#cccccc"; DARK_INSERT_BG = "#555555"
CANVAS_BG = "#1e1e1e"; SETTLEMENT_COLOR = "#4a90e2"; WEALTH_TEXT_COLOR = "#ffffff"
TRADE_ROUTE_COLOR = "#f5a623"; TRADE_ROUTE_FLASH_COLOR = "#ffffff";

# --- Main Simulation UI Class ---
# (SimulationUI class remains the same)
class SimulationUI:
    def __init__(self, root, config_file="config.json", recipe_file="recipes.json"):
        self.root = root
        self.root.title(ui_params['window_title'])
        try: self.root.state('zoomed')
        except tk.TclError: print("WARN: Could not zoom window.")
        self.TICK_DELAY_MS = ui_params['tick_delay_ms']
        self.ANIMATION_FRAME_DELAY_MS = ui_params.get('animation_frame_delay_ms', 33)
        self.TRADE_EFFECT_DURATION_MS = ui_params['trade_effect_duration_ms']
        self.SETTLEMENT_BASE_RADIUS = ui_params['settlement_base_radius']
        self.SETTLEMENT_WEALTH_SCALE_PARAM = ui_params.get('settlement_wealth_sqrt_scale', 0.5)
        self.SETTLEMENT_MAX_RADIUS_INCREASE = ui_params['settlement_max_radius_increase']
        self.CITY_COLOR = ui_params.get('city_color', "#e27a7a")
        self.CITY_POP_THRESHOLD = sim_params_for_ui['city_population_threshold']
        self.DARK_BG = DARK_BG; self.DARK_FG = DARK_FG; self.DARK_INSERT_BG = DARK_INSERT_BG
        self.CANVAS_BG = CANVAS_BG; self.SETTLEMENT_COLOR = SETTLEMENT_COLOR; self.WEALTH_TEXT_COLOR = WEALTH_TEXT_COLOR
        self.TRADE_ROUTE_COLOR = TRADE_ROUTE_COLOR; self.TRADE_ROUTE_FLASH_COLOR = TRADE_ROUTE_FLASH_COLOR;
        self.DEFAULT_SHIPMENT_COLOR = ui_params.get('default_shipment_color', "#FFFFFF")
        self.SHIPMENT_MARKER_RADIUS = ui_params.get('shipment_marker_radius', 3)
        self.SHIPMENT_MARKER_OFFSET = ui_params.get('shipment_marker_offset', 4)
        self.SV_TTK_AVAILABLE = SV_TTK_AVAILABLE
        self._apply_theme()
        self.simulation_running = False
        self.last_tick_time = 0
        self.next_tick_target_time = 0
        print("Setting up world...")
        try:
            self.tick_duration_sec = self.TICK_DELAY_MS / 1000.0
            if self.tick_duration_sec <= 0: self.tick_duration_sec = 1.0
            self.world = setup_world(config_file=config_file, recipe_file=recipe_file, tick_duration_sec=self.tick_duration_sec)
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = self.world.get_all_settlements(include_abandoned=True)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            self.good_colors = self._assign_good_colors()
            print("World setup complete.")
        except Exception as e:
            print(f"\n--- ERROR DURING WORLD SETUP ---"); print(e); traceback.print_exc(); self.root.quit(); return
        self.settlements_tree = None; self.goods_tree = None; self.recipe_text = None; self.global_totals_tree = None
        self.avg_prices_tree = None; self.trade_volume_tree = None
        self.scrollable_canvas = None; self.scrollable_frame = None; self.canvas_frame_id = None
        self.settlement_widgets = {}
        self.map_canvas = None; self.settlement_canvas_items = {}; self.shipment_markers = {}
        self.goods_legend_frame = None; self.settlement_font = tkFont.Font(family="Arial", size=9)
        self.wealth_font = tkFont.Font(family="Arial", size=10, weight="bold")
        self.legend_font = tkFont.Font(family="Arial", size=8)
        self.analysis_window = None; self.analysis_tree_potential = None; self.analysis_tree_failed = None
        self.analysis_tree_executed = None; self.analysis_tree_migration = None
        self.last_trade_info_var = tk.StringVar(value="No trades yet this tick.")
        self.last_trade_reason_var = tk.StringVar(value="")
        self.tick_label_var = tk.StringVar(value="Tick: 0")
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1, minsize=300); self.main_frame.columnconfigure(1, weight=6, minsize=600)
        self.main_frame.rowconfigure(1, weight=1)
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.tick_label = ttk.Label(control_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        self.tick_label.pack(side=tk.LEFT, padx=(0, 20))
        self.start_button = ttk.Button(control_frame, text="Start", command=self._start_sim, state=tk.NORMAL)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self._pause_sim, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        analysis_button = ttk.Button(control_frame, text="Trade Analysis", command=lambda: ui_analysis_window.open_analysis_window(self))
        analysis_button.pack(side=tk.LEFT, padx=5)
        self.static_pane_frame = ttk.Frame(self.main_frame, padding="5")
        self.static_pane_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        ui_static_pane.setup_static_pane(self.static_pane_frame, self)
        self._setup_notebook()
        print("Starting simulation and animation loops (initially paused)...")
        try:
            ui_map_pane.create_settlement_canvas_items(self)
            ui_dynamic_pane.update_dynamic_pane(self)
            ui_static_pane.update_static_pane(self)
            self.last_tick_time = time.perf_counter()
            self.next_tick_target_time = self.last_tick_time + self.tick_duration_sec
            self.root.after(10, self.update_simulation)
            self.root.after(self.ANIMATION_FRAME_DELAY_MS, self._update_animation_frame)
        except Exception as e:
            print(f"\n--- ERROR ON FIRST SIMULATION START ---"); print(e); traceback.print_exc(); self.root.quit()
    def _assign_good_colors(self):
        colors = {}
        if not hasattr(self, 'world') or not self.world.goods: return colors
        for good_id, good_obj in self.world.goods.items():
            colors[good_id] = getattr(good_obj, 'color', self.DEFAULT_SHIPMENT_COLOR)
            if not isinstance(colors[good_id], str) or not colors[good_id].startswith('#'): colors[good_id] = self.DEFAULT_SHIPMENT_COLOR
        return colors
    def _pause_sim(self):
        if self.simulation_running:
            self.simulation_running = False; self.pause_button.config(state=tk.DISABLED); self.start_button.config(state=tk.NORMAL)
            print("--- Simulation Paused ---")
    def _start_sim(self):
        if not self.simulation_running:
            self.simulation_running = True; self.pause_button.config(state=tk.NORMAL); self.start_button.config(state=tk.DISABLED)
            print("--- Simulation Resumed ---")
            self.last_tick_time = time.perf_counter(); self.next_tick_target_time = self.last_tick_time + self.tick_duration_sec
            self.root.after(10, self.update_simulation)
    def _apply_theme(self):
        if self.SV_TTK_AVAILABLE: sv_ttk.set_theme("dark"); self.root.configure(bg=self.DARK_BG)
        else:
             style = ttk.Style(); theme_to_use = 'clam' if 'clam' in style.theme_names() else 'alt'
             try: style.theme_use(theme_to_use)
             except tk.TclError: print(f"WARN: Could not use theme '{theme_to_use}'.")
             self.root.config(bg=self.DARK_BG); style.configure('.', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('TFrame', background=self.DARK_BG); style.configure('TLabel', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('TLabelFrame', background=self.DARK_BG, foreground=self.DARK_FG); style.configure('TLabelFrame.Label', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('Treeview', background="#3f3f3f", foreground=self.DARK_FG, fieldbackground="#3f3f3f")
             style.configure('Treeview.Heading', background="#4a4a4a", foreground=self.DARK_FG); style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
             style.configure('TScrollbar', background=self.DARK_BG, troughcolor="#4a4a4a"); style.configure("TNotebook", background=self.DARK_BG, borderwidth=0)
             style.configure("TNotebook.Tab", background="#4a4a4a", foreground=self.DARK_FG, padding=[5, 2], borderwidth=0); style.map("TNotebook.Tab", background=[("selected", self.SETTLEMENT_COLOR)], foreground=[("selected", "white")])
    def _setup_notebook(self):
        self.notebook = ttk.Notebook(self.main_frame); self.notebook.grid(row=1, column=1, sticky="nsew", padx=(5,0))
        self.dynamic_pane_frame = ttk.Frame(self.notebook, padding="5"); self.dynamic_pane_frame.grid(row=0, column=0, sticky="nsew")
        self.dynamic_pane_frame.rowconfigure(0, weight=1); self.dynamic_pane_frame.columnconfigure(0, weight=1)
        ui_dynamic_pane.setup_dynamic_pane(self.dynamic_pane_frame, self)
        self.viz_pane_frame = ttk.Frame(self.notebook, padding="5"); self.viz_pane_frame.grid(row=0, column=0, sticky="nsew")
        self.viz_pane_frame.columnconfigure(0, weight=1); self.viz_pane_frame.columnconfigure(1, weight=0, minsize=100); self.viz_pane_frame.rowconfigure(0, weight=1)
        ui_map_pane.setup_map_pane(self.viz_pane_frame, self); self.notebook.add(self.dynamic_pane_frame, text='Settlement Details'); self.notebook.add(self.viz_pane_frame, text='Map')
    def update_simulation(self):
        if not self.simulation_running: self.root.after(100, self.update_simulation); return
        if not self.root.winfo_exists(): print("Root window closed."); return
        try:
            current_time = time.perf_counter(); self.last_tick_time = current_time
            self.world.simulation_step()
            self.tick_label_var.set(f"Tick: {self.world.tick}"); self.settlements = self.world.get_all_settlements(include_abandoned=True)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}; self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            ui_static_pane.update_static_pane(self); ui_dynamic_pane.update_dynamic_pane(self); ui_map_pane.update_map_pane_tick_based(self); ui_analysis_window.update_analysis_window(self)
            processing_end_time = time.perf_counter(); processing_time_sec = processing_end_time - self.last_tick_time
            target_delay_sec = self.tick_duration_sec; self.next_tick_target_time += target_delay_sec
            current_time_after_processing = time.perf_counter(); delay_sec = self.next_tick_target_time - current_time_after_processing
            delay_ms = max(1, int(delay_sec * 1000))
            if self.simulation_running: self.root.after(delay_ms, self.update_simulation)
        except Exception as e: print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---"); traceback.print_exc(); self.root.quit()
    def _update_animation_frame(self):
        if not self.root.winfo_exists(): return
        if not self.simulation_running: self.root.after(self.ANIMATION_FRAME_DELAY_MS, self._update_animation_frame); return
        try:
            ui_map_pane.update_shipment_marker_positions_smoothly(self); self.root.after(self.ANIMATION_FRAME_DELAY_MS, self._update_animation_frame)
        except Exception as e: print(f"\n--- ERROR DURING ANIMATION FRAME UPDATE ---"); traceback.print_exc(); self.root.after(self.ANIMATION_FRAME_DELAY_MS, self._update_animation_frame)


# --- Headless Mode Function ---
def run_headless_simulation(args):
    """
    Sets up and runs the simulation in headless mode based on CLI arguments.
    Includes periodic console output and optional delay.
    """
    print("\n--- Starting Headless Simulation ---")
    print(f"  Mode:          {args.mode}")
    print(f"  Max Ticks:     {args.ticks if args.ticks else 'Run indefinitely'}")
    print(f"  Config File:   {args.config}")
    print(f"  Recipe File:   {args.recipes}")
    print(f"  Output File:   {args.output if args.output else 'None'}")
    if args.mode == 'continuous':
        print(f"  Delay (sec):   {args.delay:.2f}")
        print(f"  Clear Screen:  {not args.no_clear}")
    print(f"  Print Interval:{args.print_interval}")
    print("-" * 35)

    print_interval = args.print_interval

    try:
        # 1. Setup World
        world = setup_world(config_file=args.config,
                            recipe_file=args.recipes,
                            tick_duration_sec=1.0) # Nominal duration

        # 2. Simulation Loop
        tick_limit = args.ticks
        current_tick = 0
        start_time = time.perf_counter()

        while True:
            # Check termination condition
            if tick_limit is not None and current_tick >= tick_limit:
                if tick_limit > 0 and tick_limit % print_interval != 0:
                    if args.mode == 'continuous' and not args.no_clear:
                         os.system('cls' if os.name == 'nt' else 'clear')
                    _print_headless_summary(world, current_tick)
                print(f"\nReached tick limit ({tick_limit}). Stopping.")
                break

            loop_start_time = time.perf_counter()

            # Execute simulation step
            world.simulation_step()
            current_tick = world.tick

            # --- Periodic Console Output ---
            if current_tick == 1 or current_tick % print_interval == 0:
                 if args.mode == 'continuous' and not args.no_clear:
                     os.system('cls' if os.name == 'nt' else 'clear')
                 _print_headless_summary(world, current_tick) # Call helper function

                 active_settlements = world.get_all_settlements(include_abandoned=False)
                 if not active_settlements and current_tick > 0:
                     print(f"\nAll settlements abandoned at tick {current_tick}. Stopping.")
                     break

            # --- Continuous Mode Delay ---
            if args.mode == 'continuous':
                loop_end_time = time.perf_counter()
                loop_duration = loop_end_time - loop_start_time
                sleep_time = max(0.01, args.delay - loop_duration)
                time.sleep(sleep_time)

        end_time = time.perf_counter()
        duration = end_time - start_time
        final_tick_count = current_tick if tick_limit is None or current_tick <= tick_limit else tick_limit

        print(f"\n--- Headless Simulation Finished ---")
        print(f"  Total Ticks Run: {final_tick_count}")
        print(f"  Total Duration:  {duration:.2f} seconds")
        if final_tick_count > 0:
             avg_tick_time = duration / final_tick_count
             print(f"  Average Tick Time: {avg_tick_time:.4f} seconds")

        # 3. TODO: Implement summary output to args.output file if specified
        if args.output:
            print(f"\nAttempting to save summary to: {args.output} (Not Implemented)")
            pass

    except KeyboardInterrupt:
         print("\n--- Simulation Interrupted by User (Ctrl+C) ---")
         if 'world' in locals():
             if args.mode == 'continuous' and not args.no_clear:
                 os.system('cls' if os.name == 'nt' else 'clear')
             _print_headless_summary(world, world.tick)
         sys.exit(0)
    except Exception as e:
        print(f"\n--- ERROR DURING HEADLESS SIMULATION ---")
        traceback.print_exc()
        sys.exit(1)

# --- Helper Functions for Headless Printing ---

def _format_settlement_details(s, world, widths):
    """Formats the detailed block for a single settlement as a list of strings."""
    lines = []
    NAME_W, NUM_W, FLOAT_W, GOOD_NAME_W = widths

    # Header
    lines.append(f"{C_SETTLEMENT}--- {s.name:<{NAME_W}} ({s.id}) ---{C_RESET}")

    # Basic Stats
    storage_load = s.get_current_storage_load()
    pop_str = f"{s.population:,.0f}"
    wealth_str = f"{s.wealth:,.1f}"
    cur_labor_str = f"{s.current_labor_pool:.1f}"
    max_labor_str = f"{s.max_labor_pool:.1f}"
    cur_store_str = f"{storage_load:.1f}"
    max_store_str = f"{s.storage_capacity:.0f}"
    trades_str = f"{s.trades_executed_this_tick}/{s.trade_capacity}"
    food_t_str = f"{C_WARN if s.ticks_below_food_threshold > 0 else C_VALUE}{s.ticks_below_food_threshold}{C_RESET}"
    wealth_t_str = f"{C_WARN if s.ticks_below_wealth_threshold > 0 else C_VALUE}{s.ticks_below_wealth_threshold}{C_RESET}"

    lines.append(f" Pop: {C_VALUE}{pop_str:>{NUM_W}}{C_RESET} | Wealth: {C_VALUE}{wealth_str:>{FLOAT_W}}{C_RESET} | MktLvl: {C_VALUE}{s.market_level:<{NUM_W-5}}{C_RESET} | Trades: {C_VALUE}{trades_str:<{NUM_W-3}}{C_RESET}")
    lines.append(f" Labor: {C_VALUE}{cur_labor_str:>{NUM_W-2}}/{max_labor_str:<{NUM_W-2}}{C_RESET} | Storage: {C_VALUE}{cur_store_str:>{NUM_W-1}}/{max_store_str:<{NUM_W-1}}{C_RESET} | FoodT: {food_t_str:<{NUM_W-5}} | WealthT: {wealth_t_str:<{NUM_W-5}}")

    # Inventory (Fixed Height)
    lines.append(f" {C_GOOD}Inventory:{C_RESET}")
    sorted_goods = sorted(world.goods.values(), key=lambda g: g.name)
    for good in sorted_goods:
         stock = s.get_total_stored(good.id)
         price = s.local_prices.get(good.id, 0.0)
         stock_str = f"{stock:.1f}"
         price_str = f"{price:.2f}"
         line_color = C_VALUE if stock > 1e-6 else C_SUBTLE
         lines.append(f"   - {good.name:<{GOOD_NAME_W}} : {line_color}{stock_str:<{FLOAT_W}}{C_RESET} (@ {line_color}{price_str:<{FLOAT_W-2}}{C_RESET})")

    # Production (Dynamic Height)
    lines.append(f" {C_GOOD}Production (Tick):{C_RESET}")
    has_production = False
    sorted_prod = sorted(s.production_this_tick.items(), key=lambda item: world.goods[item[0]].name)
    for gid, qty in sorted_prod:
        if qty > 1e-6:
            has_production = True
            lines.append(f"   - {world.goods[gid].name:<{GOOD_NAME_W}} : {C_VALUE}{qty:.1f}{C_RESET}")
    if not has_production:
         lines.append(f"{C_SUBTLE}   (None){C_RESET}")

    # Needs (Fixed Height - List ALL potentially consumed goods)
    # Let's assume non-TOOL goods might be consumed
    lines.append(f" {C_GOOD}Needs:{C_RESET}")
    # We iterate through sorted goods again to ensure fixed order/height
    has_needs = False
    for good in sorted_goods:
         # Optionally filter which goods appear in Needs list, e.g., exclude TOOLS
         # if good.good_type == 'TOOL': continue

         multiplier = s.consumption_needs.get(good.id, 1.0) # Use .get for safety
         if multiplier > 1.01:
             has_needs = True
             # Highlight need value in warning color
             lines.append(f"   - {good.name:<{GOOD_NAME_W}} : {C_WARN}{multiplier:.2f}x{C_RESET}")
         # To fix height, uncomment the else block:
         # else:
         #      lines.append(f"{C_SUBTLE}   - {good.name:<{GOOD_NAME_W}} : {multiplier:.2f}x{C_RESET}")

    # If we didn't print any needs because none were > 1.01 (and didn't uncomment the else block)
    # We need to add placeholder lines to match the full height if strict fixed height is desired
    # For now, let's keep it dynamic unless explicitly adding all goods above.
    # If has_needs is False (and no else block used):
    if not has_needs:
         lines.append(f"{C_SUBTLE}   (Normal){C_RESET}")


    return lines


def _print_headless_summary(world, tick):
    """Prints the detailed periodic summary to the console with colors and fixed-height inventory."""
    # Define fixed widths
    NAME_W = 15; ID_W = 4; NUM_W = 7; FLOAT_W = 10; GOOD_NAME_W = 10
    COL_GAP = 4 # Space between columns
    COL_WIDTH = 75 # Estimated width for one settlement's details block

    print(f"\n{C_HEADER}{C_BOLD}{'='*15} TICK: {tick} {'='*(COL_WIDTH*2+COL_GAP-24-len(str(tick)))}{C_RESET}")
    active_settlements = world.get_all_settlements(include_abandoned=False)
    total_pop = sum(s.population for s in active_settlements)
    total_wealth = sum(s.wealth for s in active_settlements)
    avg_wealth = total_wealth / len(active_settlements) if active_settlements else 0

    # --- Global Stats ---
    print(f"{C_HEADER}--- Global ---{C_RESET}")
    print(f" Active Sett: {C_VALUE}{len(active_settlements):<{NUM_W-1}}{C_RESET} | Total Pop: {C_VALUE}{total_pop:<{NUM_W+2},.0f}{C_RESET} | Total Wealth: {C_VALUE}{total_wealth:<{FLOAT_W+3},.1f}{C_RESET} | Avg Wealth: {C_VALUE}{avg_wealth:<{FLOAT_W+1},.1f}{C_RESET}")
    print(f"{C_SUBTLE}{'-'*(COL_WIDTH*2+COL_GAP)}{C_RESET}") # Separator spanning two columns

    # --- Settlements Details (Two Columns) ---
    sorted_settlements = sorted(active_settlements, key=lambda sett: sett.id)
    num_settlements = len(sorted_settlements)
    widths = (NAME_W, NUM_W, FLOAT_W, GOOD_NAME_W)

    for i in range(0, num_settlements, 2):
        s_left = sorted_settlements[i]
        s_right = sorted_settlements[i+1] if (i+1) < num_settlements else None

        lines_left = _format_settlement_details(s_left, world, widths)
        lines_right = _format_settlement_details(s_right, world, widths) if s_right else []

        max_lines = max(len(lines_left), len(lines_right))

        # Pad shorter list with empty strings for zip
        lines_left.extend([''] * (max_lines - len(lines_left)))
        lines_right.extend([''] * (max_lines - len(lines_right)))

        # Print lines side-by-side
        for l_left, l_right in zip(lines_left, lines_right):
            # Calculate padding for left column to align right column
            # Need to account for invisible ANSI codes in width calculation
            len_left_visible = len(re.sub(r'\033\[\d+(;\d+)?m', '', l_left)) # Simple regex remove ANSI
            padding = max(0, COL_WIDTH - len_left_visible)
            print(f"{l_left}{' '*padding}{' '*COL_GAP}{l_right}")

        # Print separator only if there was a right column, or if it's not the last row
        if s_right or (i+2) < num_settlements:
             print(f"{C_SUBTLE}{'-'*(COL_WIDTH*2+COL_GAP)}{C_RESET}")

    # If no settlements, print a message
    if num_settlements == 0:
        print(f"{C_WARN}No active settlements.{C_RESET}")
        print(f"{C_SUBTLE}{'-'*(COL_WIDTH*2+COL_GAP)}{C_RESET}")

    print(f"{C_BOLD}{'='*(COL_WIDTH*2+COL_GAP)}{C_RESET}\n") # End of summary block separator


# Regex needed for stripping ANSI codes for width calculation
import re

# --- Main Execution Block ---
if __name__ == "__main__":
    """Entry point for the application. Parses CLI args for headless mode."""

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Run the Emergent Trade Simulation",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--headless', action='store_true', help='Run headless.')
    parser.add_argument('--ticks', type=int, default=None, help='Ticks to run.')
    parser.add_argument('--config', type=str, default='config.json', help='Config file.')
    parser.add_argument('--recipes', type=str, default='recipes.json', help='Recipes file.')
    parser.add_argument('--output', type=str, default=None, help='Output summary file.')
    parser.add_argument('--mode', type=str, choices=['instant', 'continuous'], default='instant',
                        help="Execution mode: 'instant' runs fast, 'continuous' runs with delay.")
    parser.add_argument('--delay', type=float, default=1.0,
                        help='Delay in seconds between ticks for continuous mode (min 0.01).')
    parser.add_argument('--print_interval', type=int, default=50,
                        help='Frequency of console summary printing (every N ticks).')
    parser.add_argument('--no-clear', action='store_true', # Added --no-clear
                        help='Disable screen clearing in continuous mode.')

    args = parser.parse_args()

    # --- Argument Validation ---
    if args.mode == 'continuous' and args.delay < 0.01:
        print("WARN: Specified delay is less than 0.01s. Using 0.01s instead.")
        args.delay = 0.01
    if args.print_interval < 1:
        print("WARN: Specified print_interval is less than 1. Using 1 instead.")
        args.print_interval = 1

    # --- Mode Selection ---
    if args.headless:
        run_headless_simulation(args)
        sys.exit(0)
    else:
        # Load config needed for UI elements before creating the root window
        load_configuration(args.config)

        root = tk.Tk()
        try:
            # Pass config/recipe file paths to the UI/World setup
            app = SimulationUI(root, config_file=args.config, recipe_file=args.recipes)
            root.mainloop()
        except Exception as e:
            print(f"\n--- FATAL ERROR INITIALIZING UI ---")
            traceback.print_exc()
        finally:
            print("UI Closed / Application Finished.")