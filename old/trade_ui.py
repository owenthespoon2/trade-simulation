import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import time
import textwrap
import traceback
import random
import json
import sys
import math
from collections import Counter, defaultdict

# ==============================================================================
# FILE INDEX
# ==============================================================================
# - Imports & Theme Setup                 : Line 1
# - Load UI/Sim Configuration             : Line 24
# - UI Constants                          : Line 50
# - SimulationUI Class                    : Line 64
#   - __init__                            : Line 65 (Added settlement_widgets dict)
#   - Control Methods (_pause_sim, etc.)  : Line 104
#   - Theme Application (_apply_theme)    : Line 113
#   - UI Setup Methods
#     - _setup_static_pane                : Line 126
#     - _setup_notebook                   : Line 161
#     - _setup_dynamic_widgets            : Line 169 (Scrollable setup)
#     - _setup_visualization_widgets      : Line 196
#   - Treeview Creation/Update Methods
#     - _create_settlements_treeview      : Line 211
#     - _create_goods_treeview            : Line 224
#     - _on_good_select                   : Line 232
#     - _update_recipe_display            : Line 242
#   - Visualization Drawing Methods
#     - _calculate_settlement_radius      : Line 248
#     - _create_settlement_canvas_items   : Line 256
#     - _update_settlement_visuals        : Line 268
#     - _create_single_settlement_item    : Line 290
#     - _draw_trade_route                 : Line 298
#     - _set_item_color / _delete_canvas_item : Line 315
#   - Trade Analysis Window Methods
#     - _open_trade_analysis_window       : Line 324
#     - _create_analysis_treeview         : Line 356
#     - _sort_treeview_column             : Line 370
#     - _update_trade_analysis_window     : Line 380
#     - _on_analysis_window_close         : Line 436
#   - Main Update Loop (update_simulation): Line 441
#   - UI Update Helper Methods
#     - _update_global_totals_display     : Line 492
#     - _update_dynamic_widgets           : Line 505
#     - _create_settlement_detail_widgets : Line 532 (MODIFIED - Added Padding)
#     - _update_settlement_detail_widgets : Line 573
#   - Scrollable Frame Helpers            : Line 177 (_on_frame_configure, etc.)
# - Main Execution Block                  : Line 607
# ==============================================================================


# --- Import ttk theme library (Optional but recommended for dark mode) ---
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    print("WARN: 'sv_ttk' library not found. UI will use default theme.")
    SV_TTK_AVAILABLE = False

# --- Import Simulation Logic & Setup ---
try:
    from trade_logic import World, Good, Settlement, ItemInstance
except ImportError: print("ERROR: Make sure 'trade_logic.py' exists and is runnable."); sys.exit(1)
try: from world_setup import setup_world
except ImportError: print("ERROR: Make sure 'world_setup.py' exists and is runnable."); sys.exit(1)

# --- Load UI Configuration ---
DEFAULT_UI_PARAMS = {
    "tick_delay_ms": 1000, "trade_effect_duration_ms": 1200, "settlement_radius": 15,
    "trade_marker_radius": 4, "window_title": "Emergent Trade Simulation", "settlement_base_radius": 8,
    "settlement_wealth_scale": 4.0, "settlement_wealth_sqrt_scale": 0.5,
    "settlement_max_radius_increase": 25, "city_color": "#e27a7a"
}
DEFAULT_SIM_PARAMS = { "city_population_threshold": 150 }

ui_params = DEFAULT_UI_PARAMS.copy()
sim_params_for_ui = DEFAULT_SIM_PARAMS.copy()
try:
    with open("config.json", 'r') as f: config_data = json.load(f)
    loaded_ui_params = config_data.get("ui_parameters", {}); loaded_sim_params = config_data.get("simulation_parameters", {})
    ui_params.update(loaded_ui_params)
    sim_params_for_ui['city_population_threshold'] = loaded_sim_params.get('city_population_threshold', DEFAULT_SIM_PARAMS['city_population_threshold'])
    print(f"Loaded UI parameters from config.json: {ui_params}")
except FileNotFoundError: print("WARN: config.json not found. Using default UI parameters.")
except json.JSONDecodeError: print("ERROR: Could not decode config.json. Using default UI parameters.")
except Exception as e: print(f"ERROR loading UI parameters from config.json: {e}. Using defaults.")

# --- UI Constants ---
TICK_DELAY_MS = ui_params['tick_delay_ms']
WINDOW_TITLE = ui_params['window_title']
TRADE_EFFECT_DURATION_MS = ui_params['trade_effect_duration_ms']
SETTLEMENT_BASE_RADIUS = ui_params['settlement_base_radius']
SETTLEMENT_WEALTH_SCALE_PARAM = ui_params.get('settlement_wealth_sqrt_scale', 0.5)
SETTLEMENT_MAX_RADIUS_INCREASE = ui_params['settlement_max_radius_increase']
TRADE_MARKER_RADIUS = ui_params['trade_marker_radius']
CITY_COLOR = ui_params.get('city_color', "#e27a7a")
CITY_POP_THRESHOLD = sim_params_for_ui['city_population_threshold']

# Theme colors
DARK_BG = "#2e2e2e"; DARK_FG = "#cccccc"; DARK_INSERT_BG = "#555555"
CANVAS_BG = "#1e1e1e"; SETTLEMENT_COLOR = "#4a90e2"; WEALTH_TEXT_COLOR = "#ffffff"
TRADE_ROUTE_COLOR = "#f5a623"; TRADE_ROUTE_FLASH_COLOR = "#ffffff"; TRADE_MARKER_COLOR = "#50e3c2"

# --- Main Simulation UI Class ---
class SimulationUI:
    """Manages the Tkinter user interface for the trade simulation."""

    def __init__(self, root):
        """Initializes the UI, sets up the world, and creates widgets."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        try: self.root.state('zoomed')
        except tk.TclError: print("WARN: Could not zoom window.")

        self._apply_theme()
        self.simulation_running = True

        # Analysis window references
        self.analysis_window = None; self.analysis_tree_potential = None
        self.analysis_tree_failed = None; self.analysis_tree_executed = None
        self.analysis_tree_migration = None

        # Widget Storage for Dynamic Updates
        self.settlement_widgets = {} # Stores {settlement_id: {widget_name: widget_ref}}

        print("Setting up world...")
        try:
            self.world = setup_world(config_file="config.json", recipe_file="recipes.json")
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            self.settlement_canvas_items = {}
            print("World setup complete.")
        except Exception as e:
            print(f"\n--- ERROR DURING WORLD SETUP ---"); print(e); traceback.print_exc(); self.root.quit(); return

        # Tkinter variables
        self.last_trade_info_var = tk.StringVar(value="No trades yet this tick.")
        self.last_trade_reason_var = tk.StringVar(value="")
        self.tick_label_var = tk.StringVar(value="Tick: 0")

        # Create Main UI Frames
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1, minsize=300)
        self.main_frame.columnconfigure(1, weight=4, minsize=600)
        self.main_frame.rowconfigure(1, weight=1)

        # Control Bar
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.tick_label = ttk.Label(control_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        self.tick_label.pack(side=tk.LEFT, padx=(0, 20))
        self.start_button = ttk.Button(control_frame, text="Start", command=self._start_sim, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self._pause_sim, state=tk.NORMAL)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        analysis_button = ttk.Button(control_frame, text="Trade Analysis", command=self._open_trade_analysis_window)
        analysis_button.pack(side=tk.LEFT, padx=5)

        # Setup Main Content Areas
        self._setup_static_pane()
        self._setup_notebook()

        print("Starting simulation loop...")
        try:
             self._create_settlement_canvas_items()
             self._update_dynamic_widgets() # Initial population of dynamic widgets
             self._update_global_totals_display() # Initial population of global totals
             if self.simulation_running: self.root.after(TICK_DELAY_MS, self.update_simulation)
        except Exception as e:
             print(f"\n--- ERROR ON FIRST SIMULATION START ---"); print(e); traceback.print_exc(); self.root.quit()

    # --- Simulation Control Methods ---
    def _pause_sim(self):
        if self.simulation_running:
            self.simulation_running = False; self.pause_button.config(state=tk.DISABLED); self.start_button.config(state=tk.NORMAL)
            print("--- Simulation Paused ---")
    def _start_sim(self):
        if not self.simulation_running:
            self.simulation_running = True; self.pause_button.config(state=tk.NORMAL); self.start_button.config(state=tk.DISABLED)
            print("--- Simulation Resumed ---"); self.root.after(10, self.update_simulation)

    # --- Theme Application ---
    def _apply_theme(self):
        if SV_TTK_AVAILABLE:
            sv_ttk.set_theme("dark"); self.root.configure(bg=DARK_BG)
        else: # Fallback theme
             print("Applying basic fallback dark theme..."); style = ttk.Style()
             theme_to_use = 'clam' if 'clam' in style.theme_names() else 'alt'
             try: style.theme_use(theme_to_use)
             except tk.TclError: print(f"WARN: Could not use theme '{theme_to_use}'. Using default.")
             self.root.config(bg=DARK_BG); style.configure('.', background=DARK_BG, foreground=DARK_FG)
             style.configure('TFrame', background=DARK_BG); style.configure('TLabel', background=DARK_BG, foreground=DARK_FG)
             style.configure('TLabelFrame', background=DARK_BG, foreground=DARK_FG); style.configure('TLabelFrame.Label', background=DARK_BG, foreground=DARK_FG)
             style.configure('Treeview', background="#3f3f3f", foreground=DARK_FG, fieldbackground="#3f3f3f")
             style.configure('Treeview.Heading', background="#4a4a4a", foreground=DARK_FG); style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
             style.configure('TScrollbar', background=DARK_BG, troughcolor="#4a4a4a"); style.configure("TNotebook", background=DARK_BG, borderwidth=0)
             style.configure("TNotebook.Tab", background="#4a4a4a", foreground=DARK_FG, padding=[5, 2], borderwidth=0); style.map("TNotebook.Tab", background=[("selected", SETTLEMENT_COLOR)], foreground=[("selected", "white")])

    # --- UI Setup Methods ---
    def _setup_static_pane(self):
        """Sets up the left pane containing static/summary information."""
        static_pane = ttk.Frame(self.main_frame, padding="5")
        static_pane.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        static_pane.rowconfigure(1, weight=1); static_pane.rowconfigure(3, weight=1)
        static_pane.rowconfigure(5, weight=1); static_pane.rowconfigure(7, weight=1)
        static_pane.columnconfigure(0, weight=1)
        # Settlements List
        ttk.Label(static_pane, text="Settlements", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        columns = ["id", "name", "terrain", "pop"]; column_names = ["ID", "Name", "Terrain", "Pop"]
        self.settlements_tree = ttk.Treeview(static_pane, columns=columns, show="headings", height=5)
        for col, name in zip(columns, column_names):
            self.settlements_tree.heading(col, text=name); width = 100; anchor = tk.W
            if col == "id": width = 30
            elif col == "pop": width = 60; anchor = tk.E
            self.settlements_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self._create_settlements_treeview(static_pane); self.settlements_tree.grid(row=1, column=0, sticky="ewns")
        settlements_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.settlements_tree.yview)
        self.settlements_tree.configure(yscrollcommand=settlements_scrollbar.set); settlements_scrollbar.grid(row=1, column=1, sticky="ns")
        # Goods List
        ttk.Label(static_pane, text="Goods", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self._create_goods_treeview(static_pane); self.goods_tree.grid(row=3, column=0, sticky="ewns")
        goods_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.goods_tree.yview)
        self.goods_tree.configure(yscrollcommand=goods_scrollbar.set); goods_scrollbar.grid(row=3, column=1, sticky="ns")
        self.goods_tree.bind("<<TreeviewSelect>>", self._on_good_select)
        # Recipe Details
        ttk.Label(static_pane, text="Recipe Details", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.recipe_text = tk.Text(static_pane, wrap=tk.WORD, state=tk.DISABLED, height=6, bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG, borderwidth=1, relief=tk.SUNKEN)
        recipe_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.recipe_text.yview)
        self.recipe_text.config(yscrollcommand=recipe_scrollbar.set); self.recipe_text.grid(row=5, column=0, sticky="ewns")
        recipe_scrollbar.grid(row=5, column=1, sticky="ns"); self._update_recipe_display("(Select a good)")
        # Global Goods Totals
        ttk.Label(static_pane, text="Global Totals", font=("Arial", 12, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        gt_cols = ["good", "total_qty"]; gt_names = ["Good", "Total Qty"]
        self.global_totals_tree = ttk.Treeview(static_pane, columns=gt_cols, show="headings", height=4)
        for col, name in zip(gt_cols, gt_names):
            self.global_totals_tree.heading(col, text=name); width = 120; anchor = tk.W
            if col == "total_qty": width = 80; anchor = tk.E
            self.global_totals_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self.global_totals_tree.grid(row=7, column=0, sticky="ewns")
        gt_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.global_totals_tree.yview)
        self.global_totals_tree.configure(yscrollcommand=gt_scrollbar.set); gt_scrollbar.grid(row=7, column=1, sticky="ns")

    def _setup_notebook(self):
        """Sets up the right pane with tabs."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=1, sticky="nsew", padx=(5,0))
        # Settlement Details Tab
        self.dynamic_pane = ttk.Frame(self.notebook, padding="5")
        self.dynamic_pane.grid(row=0, column=0, sticky="nsew")
        self.dynamic_pane.rowconfigure(0, weight=1); self.dynamic_pane.columnconfigure(0, weight=1)
        self._setup_dynamic_widgets(self.dynamic_pane) # Setup scrollable area
        # Map Tab
        self.viz_pane = ttk.Frame(self.notebook, padding="5")
        self.viz_pane.grid(row=0, column=0, sticky="nsew")
        self.viz_pane.rowconfigure(1, weight=1); self.viz_pane.columnconfigure(0, weight=1)
        self._setup_visualization_widgets(self.viz_pane)
        self.notebook.add(self.dynamic_pane, text='Settlement Details')
        self.notebook.add(self.viz_pane, text='Map')

    def _setup_dynamic_widgets(self, parent_frame):
        """Sets up the scrollable area for the 'Settlement Details' tab."""
        self.scrollable_canvas = tk.Canvas(parent_frame, bg=DARK_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.scrollable_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.scrollable_canvas)
        self.scrollable_canvas.configure(yscrollcommand=scrollbar.set)
        self.scrollable_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas_frame_id = self.scrollable_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.scrollable_canvas.bind("<Configure>", self._on_canvas_configure)
        self.scrollable_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.scrollable_canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.scrollable_canvas.bind_all("<Button-5>", self._on_mousewheel)

    # --- Scrollable Frame Helper Methods ---
    def _on_frame_configure(self, event=None):
        if hasattr(self, 'scrollable_canvas'): self.scrollable_canvas.configure(scrollregion=self.scrollable_canvas.bbox("all"))
    def _on_canvas_configure(self, event=None):
        if hasattr(self, 'scrollable_canvas') and hasattr(self, 'canvas_frame_id'): self.scrollable_canvas.itemconfig(self.canvas_frame_id, width=event.width)
    def _on_mousewheel(self, event):
        if hasattr(self, 'scrollable_canvas'):
            if event.num == 5 or event.delta < 0: self.scrollable_canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0: self.scrollable_canvas.yview_scroll(-1, "units")
    # --- End Scrollable Frame Helpers ---

    def _setup_visualization_widgets(self, parent_frame):
        """Sets up widgets for the 'Map' tab."""
        ttk.Label(parent_frame, text="Trade Map", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.map_canvas = tk.Canvas(parent_frame, bg=CANVAS_BG, width=500, height=400, highlightthickness=0)
        self.map_canvas.grid(row=1, column=0, sticky="nsew")
        self.settlement_font = tkFont.Font(family="Arial", size=9); self.wealth_font = tkFont.Font(family="Arial", size=10, weight="bold")
        info_frame = ttk.LabelFrame(parent_frame, text="Last Trade Details (This Tick)", padding="5")
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0)); info_frame.columnconfigure(0, weight=1)
        ttk.Label(info_frame, textvariable=self.last_trade_info_var, wraplength=450).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(info_frame, textvariable=self.last_trade_reason_var).grid(row=1, column=0, sticky=tk.W)

    # --- Treeview Creation/Update Methods ---
    def _create_settlements_treeview(self, parent):
        """(Re)Creates and populates the static settlements list treeview."""
        if hasattr(self, 'settlements_tree') and self.settlements_tree.winfo_exists():
            for item in self.settlements_tree.get_children():
                try: self.settlements_tree.delete(item)
                except tk.TclError: pass
            for settlement in self.settlements:
                pop_display = int(round(settlement.population))
                values = [settlement.id, settlement.name, settlement.terrain_type, pop_display]
                try: self.settlements_tree.insert("", tk.END, iid=settlement.id, values=values)
                except tk.TclError: pass

    def _create_goods_treeview(self, parent):
        """Creates and populates the static goods list treeview."""
        columns = ["id", "name", "base_value", "producible"]; column_names = ["ID", "Name", "Base Val", "Prod?"]
        self.goods_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        for col, name in zip(columns, column_names):
            self.goods_tree.heading(col, text=name); width = 80; anchor = tk.W
            if col == "base_value": anchor = tk.E
            self.goods_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        for good in self.sorted_goods:
            values = [good.id, good.name, f"{good.base_value:.1f}", "Yes" if good.is_producible else "No"]
            self.goods_tree.insert("", tk.END, iid=good.id, values=values)

    def _on_good_select(self, event):
        """Callback function when a good is selected in the goods_tree."""
        selected_items = self.goods_tree.selection()
        if not selected_items: self._update_recipe_display("(Select a good)"); return
        selected_good = self.world.goods.get(selected_items[0])
        if selected_good and selected_good.recipe:
            recipe = selected_good.recipe; recipe_str = f"** {selected_good.name} ({selected_good.id}) **\n"
            inputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['inputs'].items()]) if recipe['inputs'] else "None"; recipe_str += f"  Inputs: {inputs_str}\n"
            outputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['outputs'].items()]); recipe_str += f"  Outputs: {outputs_str}\n"; recipe_str += f"  Labor: {recipe['labor']:.1f}\n"
            if recipe['wealth_cost'] > 0: recipe_str += f"  Wealth Cost: {recipe['wealth_cost']:.1f}\n"
            if recipe['required_terrain']: recipe_str += f"  Requires: {', '.join(recipe['required_terrain'])}\n"
            self._update_recipe_display(recipe_str)
        elif selected_good: self._update_recipe_display(f"** {selected_good.name} ({selected_good.id}) **\n\n(Not producible)")
        else: self._update_recipe_display("(Error: Good not found)")

    def _update_recipe_display(self, text_content):
        """Updates the content of the recipe details text area."""
        if hasattr(self, 'recipe_text') and self.recipe_text.winfo_exists():
            self.recipe_text.config(state=tk.NORMAL); self.recipe_text.delete('1.0', tk.END)
            self.recipe_text.insert(tk.END, text_content); self.recipe_text.config(state=tk.DISABLED)

    # --- Visualization Drawing Methods ---
    def _calculate_settlement_radius(self, wealth):
        try: radius_increase = math.sqrt(max(0, wealth)) * SETTLEMENT_WEALTH_SCALE_PARAM
        except ValueError: radius_increase = 0
        capped_increase = min(radius_increase, SETTLEMENT_MAX_RADIUS_INCREASE)
        return SETTLEMENT_BASE_RADIUS + capped_increase

    def _create_settlement_canvas_items(self):
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        self.map_canvas.delete("settlement"); self.settlement_canvas_items.clear()
        for settlement in self.settlements:
            x, y, _ = self.settlement_coords[settlement.id]
            r = SETTLEMENT_BASE_RADIUS
            color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
            circle_id = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
            text_id = self.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=DARK_FG, font=self.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
            wealth_id = self.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=WEALTH_TEXT_COLOR, font=self.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
            self.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
        self._update_settlement_visuals()

    def _update_settlement_visuals(self):
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        valid_settlement_ids = set(s.id for s in self.settlements)
        ids_to_remove_from_canvas = set(self.settlement_canvas_items.keys()) - valid_settlement_ids
        for settlement_id in ids_to_remove_from_canvas:
            if settlement_id in self.settlement_canvas_items:
                items = self.settlement_canvas_items[settlement_id]
                for item_key in ['circle', 'text', 'wealth']:
                     if item_key in items: self._delete_canvas_item(items[item_key])
                del self.settlement_canvas_items[settlement_id]
        for settlement in self.settlements:
            settlement_id = settlement.id; items = self.settlement_canvas_items.get(settlement_id)
            items_valid = items and all(k in items and self.map_canvas.winfo_exists() and self.map_canvas.find_withtag(items[k]) for k in ['circle', 'text', 'wealth'])
            if items_valid:
                try:
                    x, y, _ = self.settlement_coords[settlement.id]; wealth = settlement.wealth
                    new_r = self._calculate_settlement_radius(wealth); circle_id = items['circle']; text_id = items['text']; wealth_id = items['wealth']
                    current_color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
                    self.map_canvas.coords(circle_id, x - new_r, y - new_r, x + new_r, y + new_r); self.map_canvas.itemconfig(circle_id, fill=current_color)
                    self.map_canvas.coords(text_id, x, y + new_r + 8); self.map_canvas.coords(wealth_id, x, y - new_r - 8)
                    self.map_canvas.itemconfig(wealth_id, text=f"W: {wealth:.0f}")
                except tk.TclError as e: print(f"WARN: TclError updating visuals for settlement {settlement_id}: {e}")
                except Exception as e: print(f"ERROR updating visuals for settlement {settlement_id}:"); traceback.print_exc()
            elif settlement_id not in self.settlement_canvas_items: self._create_single_settlement_item(settlement)

    def _create_single_settlement_item(self, settlement):
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        if settlement.id in self.settlement_canvas_items: return
        x, y, _ = self.settlement_coords[settlement.id]; r = SETTLEMENT_BASE_RADIUS
        color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
        circle_id = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
        text_id = self.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=DARK_FG, font=self.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
        wealth_id = self.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=WEALTH_TEXT_COLOR, font=self.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
        self.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
        self._update_settlement_visuals()

    def _draw_trade_route(self, trade_info):
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        seller_id = trade_info['seller_id']; buyer_id = trade_info['buyer_id']
        if seller_id not in self.settlement_coords or buyer_id not in self.settlement_coords: return
        x1, y1, _ = self.settlement_coords[seller_id]; x2, y2, _ = self.settlement_coords[buyer_id]
        trade_tag = f"trade_{seller_id}_{buyer_id}_{self.world.tick}_{random.randint(1000,9999)}"
        line_id = self.map_canvas.create_line(x1, y1, x2, y2, fill=TRADE_ROUTE_FLASH_COLOR, width=2.5, arrow=tk.LAST, tags=("trade_route", trade_tag))
        self.root.after(300, lambda lid=line_id: self._set_item_color(lid, TRADE_ROUTE_COLOR))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda lid=line_id: self._delete_canvas_item(lid))
        marker_r = TRADE_MARKER_RADIUS; dx = x1 - x2; dy = y1 - y2; dist = max(1, (dx**2 + dy**2)**0.5)
        buyer_settlement = self.world.settlements.get(buyer_id); current_buyer_radius = SETTLEMENT_BASE_RADIUS
        if buyer_settlement: current_buyer_radius = self._calculate_settlement_radius(buyer_settlement.wealth)
        offset_scale = current_buyer_radius + marker_r + 2; marker_x = x2 + (dx / dist) * offset_scale; marker_y = y2 + (dy / dist) * offset_scale
        marker_id = self.map_canvas.create_oval(marker_x - marker_r, marker_y - marker_r, marker_x + marker_r, marker_y + marker_r, fill=TRADE_MARKER_COLOR, outline="", tags=("trade_marker", trade_tag))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda mid=marker_id: self._delete_canvas_item(mid))

    def _set_item_color(self, item_id, color):
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists() and self.map_canvas.find_withtag(item_id):
                self.map_canvas.itemconfig(item_id, fill=color)
        except tk.TclError: pass
    def _delete_canvas_item(self, item_id):
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists() and self.map_canvas.find_withtag(item_id):
                self.map_canvas.delete(item_id)
        except tk.TclError: pass

    # --- Trade Analysis Window ---
    def _open_trade_analysis_window(self):
        if self.analysis_window and self.analysis_window.winfo_exists(): self.analysis_window.lift(); return
        self.analysis_window = tk.Toplevel(self.root); self.analysis_window.title(f"Trade & Migration Analysis (Tick {self.world.tick})")
        self.analysis_window.geometry("1000x700")
        try:
            if SV_TTK_AVAILABLE: sv_ttk.set_theme("dark"); self.analysis_window.configure(bg=DARK_BG)
        except Exception as e: print(f"WARN: Could not apply theme to analysis window: {e}")
        self.analysis_window.rowconfigure(0, weight=1); self.analysis_window.columnconfigure(0, weight=1)
        notebook = ttk.Notebook(self.analysis_window); notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        # Tabs...
        exec_frame = ttk.Frame(notebook, padding=5); notebook.add(exec_frame, text="Executed Trades")
        exec_frame.rowconfigure(0, weight=1); exec_frame.columnconfigure(0, weight=1)
        exec_cols = ('From', 'To', 'Good', 'Qty', 'Sell P', 'Buy P', 'Profit/U', 'Total Val')
        self.analysis_tree_executed = self._create_analysis_treeview(exec_frame, exec_cols)
        fail_frame = ttk.Frame(notebook, padding=5); notebook.add(fail_frame, text="Failed Executions")
        fail_frame.rowconfigure(0, weight=1); fail_frame.columnconfigure(0, weight=1)
        fail_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Reason')
        self.analysis_tree_failed = self._create_analysis_treeview(fail_frame, fail_cols)
        pot_frame = ttk.Frame(notebook, padding=5); notebook.add(pot_frame, text="Viable Potential Trades")
        pot_frame.rowconfigure(0, weight=1); pot_frame.columnconfigure(0, weight=1)
        pot_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q')
        self.analysis_tree_potential = self._create_analysis_treeview(pot_frame, pot_cols)
        mig_frame = ttk.Frame(notebook, padding=5); notebook.add(mig_frame, text="Migration")
        mig_frame.rowconfigure(0, weight=1); mig_frame.columnconfigure(0, weight=1)
        mig_cols = ('Tick', 'From', 'To', 'Quantity')
        self.analysis_tree_migration = self._create_analysis_treeview(mig_frame, mig_cols)
        self._update_trade_analysis_window(); self.analysis_window.protocol("WM_DELETE_WINDOW", self._on_analysis_window_close)

    def _create_analysis_treeview(self, parent, columns):
        """Helper function to create a Treeview with scrollbars."""
        frame = ttk.Frame(parent); frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview); hsb.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        for col in columns:
            anchor = tk.W; width = 90
            if col in ('Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Qty', 'Price', 'Total Val', 'Quantity', 'Tick'): anchor = tk.E; width=70
            if col == 'Reason': width = 250; anchor=tk.W
            if col == 'Good': width = 80
            if col == 'From' or col == 'To': width = 100
            tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_column(tree, c, False))
            tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        return tree

    def _sort_treeview_column(self, tv, col, reverse):
        """Sorts a Treeview column."""
        if not tv.winfo_exists(): return
        try:
            l = [];
            for k in tv.get_children(''):
                val = tv.set(k, col)
                try: l.append((float(val), k))
                except ValueError: l.append((str(val).lower(), k))
            l.sort(key=lambda t: t[0], reverse=reverse)
            for index, (val, k) in enumerate(l): tv.move(k, '', index)
            tv.heading(col, command=lambda c=col: self._sort_treeview_column(tv, c, not reverse))
        except Exception as e: print(f"Error sorting treeview column {col}: {e}")

    def _update_trade_analysis_window(self):
        """Updates the data displayed in the trade analysis window."""
        if not self.analysis_window or not self.analysis_window.winfo_exists(): return
        self.analysis_window.title(f"Trade & Migration Analysis (Tick {self.world.tick})")
        # Update tabs... (Logic unchanged)
        if hasattr(self, 'analysis_tree_executed') and self.analysis_tree_executed and self.analysis_tree_executed.winfo_exists():
            self.analysis_tree_executed.delete(*self.analysis_tree_executed.get_children())
            for trade in self.world.executed_trade_details_this_tick:
                values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['quantity']:.1f}", f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", f"{trade['quantity'] * trade['seller_price']:.1f}")
                try: self.analysis_tree_executed.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting executed trade: {e}")
        if hasattr(self, 'analysis_tree_failed') and self.analysis_tree_failed and self.analysis_tree_failed.winfo_exists():
            self.analysis_tree_failed.delete(*self.analysis_tree_failed.get_children())
            sorted_failed = sorted(self.world.failed_trades_this_tick, key=lambda x: x.get('profit_per_unit', 0), reverse=True)
            for trade in sorted_failed:
                 qty_avail_str = f"{trade.get('qty_avail', '?'):.1f}" if isinstance(trade.get('qty_avail'), (int,float)) else '?'
                 pot_qty_str = f"{trade.get('potential_qty', '?'):.1f}" if isinstance(trade.get('potential_qty'), (int,float)) else '?'
                 values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", qty_avail_str, pot_qty_str, trade.get('fail_reason', 'Unknown'))
                 try: self.analysis_tree_failed.insert("", tk.END, values=values)
                 except Exception as e: print(f"Error inserting failed trade: {e}")
        if hasattr(self, 'analysis_tree_potential') and self.analysis_tree_potential and self.analysis_tree_potential.winfo_exists():
            self.analysis_tree_potential.delete(*self.analysis_tree_potential.get_children())
            viable_potential = [t for t in self.world.potential_trades_this_tick if t.get('is_viable_prelim', False)]
            sorted_potential = sorted(viable_potential, key=lambda x: x['profit_per_unit'], reverse=True)
            for trade in sorted_potential:
                values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", f"{trade['qty_avail']:.1f}", f"{trade['potential_qty']:.1f}")
                try: self.analysis_tree_potential.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting potential trade: {e}")
        if hasattr(self, 'analysis_tree_migration') and self.analysis_tree_migration and self.analysis_tree_migration.winfo_exists():
            self.analysis_tree_migration.delete(*self.analysis_tree_migration.get_children())
            for migration in self.world.migration_details_this_tick:
                values = (migration['tick'], migration['from_name'], migration['to_name'], migration['quantity'])
                try: self.analysis_tree_migration.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting migration event: {e}")

    def _on_analysis_window_close(self):
        """Callback function when the analysis window is closed."""
        if self.analysis_window:
            self.analysis_window.destroy(); self.analysis_window = None
            self.analysis_tree_potential = None; self.analysis_tree_failed = None
            self.analysis_tree_executed = None; self.analysis_tree_migration = None

    # --- Main Update Loop ---
    def update_simulation(self):
        """Performs one tick of the simulation and updates the UI."""
        if not self.simulation_running: self.root.after(100, self.update_simulation); return
        if not self.root.winfo_exists(): print("Root window closed, stopping simulation loop."); return

        try:
            start_tick_time = time.time()
            self.world.simulation_step() # 1. Run Sim Step
            self.tick_label_var.set(f"Tick: {self.world.tick}") # 2. Update Tick Label
            # 3. Update Core Data Lists
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            # 4. Update Static Settlements List
            if hasattr(self, 'settlements_tree') and self.settlements_tree.winfo_exists(): self._create_settlements_treeview(None)
            # 5. Update Global Totals Display
            self._update_global_totals_display()
            # 6. Update Dynamic Settlement Details Pane (Optimized)
            self._update_dynamic_widgets()
            # 7. Update Trade Log
            if hasattr(self, 'trade_log_text') and self.trade_log_text.winfo_exists():
                self.trade_log_text.config(state=tk.NORMAL); self.trade_log_text.delete('1.0', tk.END)
                log_content = "\n".join(self.world.recent_trades_log) if self.world.recent_trades_log else "- No trades yet -"
                self.trade_log_text.insert(tk.END, log_content); self.trade_log_text.config(state=tk.DISABLED)
                self.trade_log_text.yview_moveto(1.0)
            # 8. Update Visualization & Analysis Window
            last_trade_details = None
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists():
                self._update_settlement_visuals()
                trades_this_tick = list(self.world.executed_trade_details_this_tick)
                if trades_this_tick:
                    for trade_info in trades_this_tick: self._draw_trade_route(trade_info)
                    last_trade_details = trades_this_tick[-1]
                else:
                    if hasattr(self, 'last_trade_info_var'): self.last_trade_info_var.set("No trades this tick.")
                    if hasattr(self, 'last_trade_reason_var'): self.last_trade_reason_var.set("")
            if last_trade_details:
                info = (f"Trade: {last_trade_details['quantity']:.1f} {last_trade_details['good_name']} " f"from {last_trade_details['seller_name']} to {last_trade_details['buyer_name']}")
                reason = (f"Reason: Sell P={last_trade_details['seller_price']:.2f}, " f"Buy P={last_trade_details['buyer_price']:.2f} " f"(Profit/U={last_trade_details['profit_per_unit']:.2f})")
                if hasattr(self, 'last_trade_info_var'): self.last_trade_info_var.set(info)
                if hasattr(self, 'last_trade_reason_var'): self.last_trade_reason_var.set(reason)
            self._update_trade_analysis_window()
            # 9. Schedule Next Update
            tick_duration = time.time() - start_tick_time
            delay = max(10, TICK_DELAY_MS - int(tick_duration * 1000))
            if self.simulation_running: self.root.after(delay, self.update_simulation)
        except Exception as e:
            print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---"); traceback.print_exc()
            if self.root.winfo_exists(): self.root.quit()

    # --- Helper methods for updating new UI elements ---
    def _update_global_totals_display(self):
        """Updates the global goods total treeview in the static pane."""
        if hasattr(self, 'global_totals_tree') and self.global_totals_tree.winfo_exists():
            self.global_totals_tree.delete(*self.global_totals_tree.get_children())
            global_totals = self.world.get_global_good_totals()
            sorted_good_ids = sorted(global_totals.keys(), key=lambda gid: self.world.goods[gid].name)
            for good_id in sorted_good_ids:
                good_name = self.world.goods[good_id].name; total_qty = global_totals[good_id]
                values = [good_name, f"{total_qty:.1f}"]
                try: self.global_totals_tree.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting global total for {good_name}: {e}")

    def _update_dynamic_widgets(self):
        """Optimized update for the dynamic settlement details pane."""
        if not hasattr(self, 'scrollable_frame') or not self.scrollable_frame.winfo_exists(): return
        current_settlement_ids = set(s.id for s in self.settlements)
        existing_widget_ids = set(self.settlement_widgets.keys())
        # Remove Widgets for Abandoned Settlements
        ids_to_remove = existing_widget_ids - current_settlement_ids
        for settlement_id in ids_to_remove:
            if settlement_id in self.settlement_widgets:
                try: self.settlement_widgets[settlement_id]['frame'].destroy()
                except tk.TclError: print(f"WARN: TclError destroying frame for removed settlement {settlement_id}")
                del self.settlement_widgets[settlement_id]
        # Add/Update Widgets for Current Settlements
        row_index = 0
        for settlement in self.settlements:
            settlement_id = settlement.id
            if settlement_id not in self.settlement_widgets: # Create widgets if new
                self.settlement_widgets[settlement_id] = self._create_settlement_detail_widgets(self.scrollable_frame, settlement)
            # Update existing widgets
            self._update_settlement_detail_widgets(settlement, self.settlement_widgets[settlement_id])
            # Ensure frame is in the correct row (in case order changes, though unlikely with current sort)
            self.settlement_widgets[settlement_id]['frame'].grid(row=row_index, column=0, sticky="ew", padx=5, pady=(0, 10))
            row_index += 1
        # Update scroll region
        self.scrollable_frame.update_idletasks()
        self._on_frame_configure()

    def _create_settlement_detail_widgets(self, parent_frame, settlement):
        """Creates the widgets for a single settlement's detail view."""
        widgets = {}
        frame = ttk.LabelFrame(parent_frame, text=f"{settlement.name} ({settlement.id})", padding=5)
        widgets['frame'] = frame
        # Configure grid columns
        frame.columnconfigure(1, weight=0) # Column for values - fixed width usually better
        frame.columnconfigure(2, weight=1) # Inventory tree - allow expansion
        frame.columnconfigure(3, weight=1) # Production tree - allow expansion

        # Create Labels
        widgets['pop_label_title'] = ttk.Label(frame, text="Population:")
        widgets['pop_label_value'] = ttk.Label(frame, text="0", width=5, anchor="e") # Add width & anchor
        widgets['wealth_label_title'] = ttk.Label(frame, text="Wealth:")
        widgets['wealth_label_value'] = ttk.Label(frame, text="0.0", width=8, anchor="e") # Add width & anchor
        widgets['labor_label_title'] = ttk.Label(frame, text="Labor:")
        widgets['labor_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=10, anchor="e") # Add width & anchor
        widgets['storage_label_title'] = ttk.Label(frame, text="Storage:")
        widgets['storage_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=10, anchor="e") # Add width & anchor

        # Grid Labels
        widgets['pop_label_title'].grid(row=0, column=0, sticky="w")
        widgets['pop_label_value'].grid(row=0, column=1, sticky="ew") # Use ew sticky
        widgets['wealth_label_title'].grid(row=1, column=0, sticky="w")
        widgets['wealth_label_value'].grid(row=1, column=1, sticky="ew") # Use ew sticky
        widgets['labor_label_title'].grid(row=2, column=0, sticky="w")
        widgets['labor_label_value'].grid(row=2, column=1, sticky="ew") # Use ew sticky
        widgets['storage_label_title'].grid(row=3, column=0, sticky="w")
        widgets['storage_label_value'].grid(row=3, column=1, sticky="ew") # Use ew sticky

        # Create Inventory Treeview
        inv_cols = ["good", "price", "stock"]; inv_names = ["Inventory", "Price", "Stock"]
        inv_tree = ttk.Treeview(frame, columns=inv_cols, show="headings", height=4)
        # <<< Added padding here to fix layout shift >>>
        inv_tree.grid(row=0, column=2, rowspan=4, sticky="nsew", padx=(10, 0)) # Added padx
        inv_tree.heading("good", text=inv_names[0]); inv_tree.column("good", width=70, anchor=tk.W, stretch=tk.NO)
        inv_tree.heading("price", text=inv_names[1]); inv_tree.column("price", width=40, anchor=tk.E, stretch=tk.NO)
        inv_tree.heading("stock", text=inv_names[2]); inv_tree.column("stock", width=40, anchor=tk.E, stretch=tk.NO)
        widgets['inv_tree'] = inv_tree

        # Create Production Treeview
        prod_cols = ["good", "produced"]; prod_names = ["Produced", "Qty"]
        prod_tree = ttk.Treeview(frame, columns=prod_cols, show="headings", height=4)
        prod_tree.grid(row=0, column=3, rowspan=4, sticky="nsew", padx=(5, 0))
        prod_tree.heading("good", text=prod_names[0]); prod_tree.column("good", width=70, anchor=tk.W, stretch=tk.NO)
        prod_tree.heading("produced", text=prod_names[1]); prod_tree.column("produced", width=40, anchor=tk.E, stretch=tk.NO)
        widgets['prod_tree'] = prod_tree

        return widgets

    def _update_settlement_detail_widgets(self, settlement, widgets):
        """Updates the content of the widgets for a single settlement."""
        # Update Labels
        widgets['pop_label_value'].config(text=f"{int(round(settlement.population))}")
        widgets['wealth_label_value'].config(text=f"{settlement.wealth:.1f}")
        widgets['labor_label_value'].config(text=f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}")
        storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
        widgets['storage_label_value'].config(text=f"{storage_load:.1f}/{storage_cap:.0f}")
        # Update Inventory Treeview
        inv_tree = widgets['inv_tree']; inv_tree.delete(*inv_tree.get_children())
        sorted_local_goods = sorted(self.world.goods.keys(), key=lambda gid: self.world.goods[gid].name)
        for good_id in sorted_local_goods:
            stock = settlement.get_total_stored(good_id)
            if stock > 1e-6:
                price = settlement.local_prices.get(good_id); price_str = f"{price:.2f}" if price is not None else "N/A"
                stock_str = f"{stock:.1f}"; good_name = self.world.goods[good_id].name
                try: inv_tree.insert("", tk.END, values=(good_name, price_str, stock_str))
                except Exception as e: print(f"Error inserting inv item {good_name}: {e}")
        # Update Production Treeview
        prod_tree = widgets['prod_tree']; prod_tree.delete(*prod_tree.get_children())
        if settlement.production_this_tick:
             sorted_prod_ids = sorted(settlement.production_this_tick.keys(), key=lambda gid: self.world.goods[gid].name)
             for good_id in sorted_prod_ids:
                 produced_qty = settlement.production_this_tick[good_id]
                 if produced_qty > 1e-6:
                     good_name = self.world.goods[good_id].name
                     try: prod_tree.insert("", tk.END, values=(good_name, f"{produced_qty:.1f}"))
                     except Exception as e: print(f"Error inserting prod item {good_name}: {e}")
        else:
            try: prod_tree.insert("", tk.END, values=("(None)", "-"))
            except Exception as e: print(f"Error inserting prod none: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    try: app = SimulationUI(root); root.mainloop()
    except Exception as e: print(f"\n--- FATAL ERROR INITIALIZING UI ---"); traceback.print_exc()
    finally: print("UI Closed / Application Finished.")

