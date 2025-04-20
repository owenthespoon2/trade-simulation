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

# --- Import ttk theme library ---
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    print("WARN: 'sv_ttk' library not found. UI will use default theme.")
    SV_TTK_AVAILABLE = False

# --- Import Simulation Logic & Setup ---
try:
    from trade_logic import World, Good, Settlement, ItemInstance
except ImportError: print("ERROR: Make sure 'trade_logic.py' exists."); sys.exit(1)
try:
    from world_setup import setup_world
except ImportError: print("ERROR: Make sure 'world_setup.py' exists."); sys.exit(1)

# --- Load UI Configuration ---
DEFAULT_UI_PARAMS = {
    "tick_delay_ms": 1000, "trade_effect_duration_ms": 1200,
    "settlement_radius": 15, "trade_marker_radius": 4,
    "window_title": "Emergent Trade Simulation", "settlement_base_radius": 8,
    "settlement_wealth_scale": 4.0, "settlement_max_radius_increase": 25,
    "city_color": "#e27a7a" # Default city color if not in config
}
DEFAULT_SIM_PARAMS = { # Need defaults for sim params used by UI if config fails
     "city_population_threshold": 150
}
ui_params = DEFAULT_UI_PARAMS.copy()
sim_params_for_ui = DEFAULT_SIM_PARAMS.copy() # Store sim params needed by UI separately
try:
    with open("config.json", 'r') as f:
        config_data = json.load(f)
        loaded_ui_params = config_data.get("ui_parameters", {})
        loaded_sim_params = config_data.get("simulation_parameters", {})
        ui_params.update(loaded_ui_params)
        # Get city threshold specifically for UI use
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
SETTLEMENT_WEALTH_SCALE = ui_params['settlement_wealth_scale']
SETTLEMENT_MAX_RADIUS_INCREASE = ui_params['settlement_max_radius_increase']
TRADE_MARKER_RADIUS = ui_params['trade_marker_radius']
CITY_COLOR = ui_params.get('city_color', "#e27a7a") # Use loaded color or default
CITY_POP_THRESHOLD = sim_params_for_ui['city_population_threshold'] # Use loaded/default threshold

DARK_BG = "#2e2e2e"; DARK_FG = "#cccccc"; DARK_INSERT_BG = "#555555"
CANVAS_BG = "#1e1e1e"; SETTLEMENT_COLOR = "#4a90e2"; WEALTH_TEXT_COLOR = "#ffffff"
TRADE_ROUTE_COLOR = "#f5a623"; TRADE_ROUTE_FLASH_COLOR = "#ffffff"; TRADE_MARKER_COLOR = "#50e3c2"

# --- Main Simulation UI Class ---
class SimulationUI:
    def __init__(self, root):
        self.root = root
        self.root.title(WINDOW_TITLE)
        try: self.root.state('zoomed')
        except tk.TclError: print("WARN: Could not zoom window.")
        self._apply_theme()
        print("Setting up world...")
        try:
            self.world = setup_world(config_file="config.json", recipe_file="recipes.json")
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            self.settlement_coords = {s.id: (s.x, s.y) for s in self.settlements}
            self.settlement_canvas_items = {}
            print("World setup complete.")
        except Exception as e: print(f"\n--- ERROR DURING WORLD SETUP ---"); print(e); traceback.print_exc(); self.root.quit(); return
        self.last_trade_info_var = tk.StringVar(value="No trades yet this tick.")
        self.last_trade_reason_var = tk.StringVar(value="")
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1, minsize=300)
        self.main_frame.columnconfigure(1, weight=4, minsize=600)
        self.main_frame.rowconfigure(1, weight=1)
        self.tick_label_var = tk.StringVar(value="Tick: 0")
        self.tick_label = ttk.Label(self.main_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        self.tick_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        self._setup_static_pane()
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5,0))
        self.dynamic_pane = ttk.Frame(self.notebook, padding="5")
        self.dynamic_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.dynamic_pane.rowconfigure(1, weight=3); self.dynamic_pane.rowconfigure(4, weight=1)
        self.dynamic_pane.columnconfigure(0, weight=1)
        self.viz_pane = ttk.Frame(self.notebook, padding="5")
        self.viz_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.viz_pane.rowconfigure(1, weight=1); self.viz_pane.rowconfigure(2, weight=0)
        self.viz_pane.columnconfigure(0, weight=1)
        self._setup_dynamic_widgets(self.dynamic_pane)
        self._setup_visualization_widgets(self.viz_pane)
        self.notebook.add(self.dynamic_pane, text='Tables')
        self.notebook.add(self.viz_pane, text='Map')
        print("Starting simulation loop...")
        try:
             self._create_settlement_canvas_items()
             self.update_simulation()
        except Exception as e: print(f"\n--- ERROR ON FIRST SIMULATION START ---"); print(e); traceback.print_exc(); self.root.quit()

    def _apply_theme(self):
        # (Theme application code remains the same)
        if SV_TTK_AVAILABLE: sv_ttk.set_theme("dark"); self.root.configure(bg=DARK_BG)
        else:
             print("Applying basic fallback dark theme...")
             style = ttk.Style(); style.theme_use('clam' if 'clam' in style.theme_names() else 'alt')
             self.root.config(bg=DARK_BG); style.configure('.', background=DARK_BG, foreground=DARK_FG)
             style.configure('TFrame', background=DARK_BG); style.configure('TLabel', background=DARK_BG, foreground=DARK_FG)
             style.configure('TLabelFrame', background=DARK_BG, foreground=DARK_FG); style.configure('TLabelFrame.Label', background=DARK_BG, foreground=DARK_FG)
             style.configure('Treeview', background="#3f3f3f", foreground=DARK_FG, fieldbackground="#3f3f3f")
             style.configure('Treeview.Heading', background="#4a4a4a", foreground=DARK_FG); style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
             style.configure('TScrollbar', background=DARK_BG, troughcolor="#4a4a4a")
             style.configure("TNotebook", background=DARK_BG, borderwidth=0)
             style.configure("TNotebook.Tab", background="#4a4a4a", foreground=DARK_FG, padding=[5, 2], borderwidth=0)
             style.map("TNotebook.Tab", background=[("selected", SETTLEMENT_COLOR)], foreground=[("selected", "white")])

    # --- Static Pane Setup ---
    def _setup_static_pane(self):
        static_pane = ttk.Frame(self.main_frame, padding="5")
        static_pane.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        static_pane.rowconfigure(1, weight=1); static_pane.rowconfigure(3, weight=1); static_pane.rowconfigure(5, weight=2)
        static_pane.columnconfigure(0, weight=1)
        ttk.Label(static_pane, text="Settlements", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        # Setup Treeview - it will be populated in _create_settlements_treeview
        columns = ["id", "name", "terrain", "pop"]; column_names = ["ID", "Name", "Terrain", "Pop"]
        self.settlements_tree = ttk.Treeview(static_pane, columns=columns, show="headings", height=8)
        for col, name in zip(columns, column_names):
            self.settlements_tree.heading(col, text=name); width = 100; anchor = tk.W
            if col == "id": width = 30
            elif col == "pop": width = 60; anchor = tk.E
            self.settlements_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self._create_settlements_treeview(static_pane) # Populate initial data
        self.settlements_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        settlements_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.settlements_tree.yview)
        self.settlements_tree.configure(yscrollcommand=settlements_scrollbar.set); settlements_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        # Rest of static pane...
        ttk.Label(static_pane, text="Goods", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self._create_goods_treeview(static_pane)
        self.goods_tree.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        goods_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.goods_tree.yview)
        self.goods_tree.configure(yscrollcommand=goods_scrollbar.set); goods_scrollbar.grid(row=3, column=1, sticky=(tk.N, tk.S))
        self.goods_tree.bind("<<TreeviewSelect>>", self._on_good_select)
        ttk.Label(static_pane, text="Recipe Details", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.recipe_text = tk.Text(static_pane, wrap=tk.WORD, state=tk.DISABLED, height=10, bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG, borderwidth=1, relief=tk.SUNKEN)
        recipe_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.recipe_text.yview)
        self.recipe_text.config(yscrollcommand=recipe_scrollbar.set); self.recipe_text.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        recipe_scrollbar.grid(row=5, column=1, sticky=(tk.N, tk.S)); self._update_recipe_display("(Select a good)")

    # --- Dynamic Widgets Setup ---
    def _setup_dynamic_widgets(self, parent_frame):
        ttk.Label(parent_frame, text="Settlement State", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        # Setup Treeview - it will be populated in _create_dynamic_treeview
        columns = ["name", "labor", "wealth", "storage"]
        column_names = ["Settlement", "Labor", "Wealth", "Storage"]
        for good in self.sorted_goods:
            columns.append(f"{good.id}_price"); column_names.append(f"{good.name} Prc")
            columns.append(f"{good.id}_stored"); column_names.append(f"{good.name} Stk")
        self.dynamic_tree = ttk.Treeview(parent_frame, columns=columns, show="headings")
        for col, name in zip(columns, column_names):
            self.dynamic_tree.heading(col, text=name); width = 70; anchor = tk.E
            if col == "name": width = 90; anchor = tk.W
            elif col == "labor": width = 80
            elif col == "storage": width = 80
            self.dynamic_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self._create_dynamic_treeview(parent_frame) # Populate initial data
        self.dynamic_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dynamic_scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.dynamic_tree.yview)
        dynamic_scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.dynamic_tree.xview)
        self.dynamic_tree.configure(yscrollcommand=dynamic_scrollbar_y.set, xscrollcommand=dynamic_scrollbar_x.set)
        dynamic_scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S)); dynamic_scrollbar_x.grid(row=2, column=0, sticky=(tk.W, tk.E))
        # Rest of dynamic pane...
        ttk.Label(parent_frame, text="Recent Trades Log", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.trade_log_text = tk.Text(parent_frame, height=8, width=80, wrap=tk.WORD, state=tk.DISABLED, bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG, borderwidth=1, relief=tk.SUNKEN )
        trade_log_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.trade_log_text.yview)
        self.trade_log_text.config(yscrollcommand=trade_log_scrollbar.set)
        self.trade_log_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        trade_log_scrollbar.grid(row=4, column=1, sticky=(tk.N, tk.S))

    # --- Visualization Widgets Setup (Unchanged) ---
    def _setup_visualization_widgets(self, parent_frame):
        ttk.Label(parent_frame, text="Trade Map", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.map_canvas = tk.Canvas(parent_frame, bg=CANVAS_BG, width=500, height=400, highlightthickness=0)
        self.map_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.settlement_font = tkFont.Font(family="Arial", size=9)
        self.wealth_font = tkFont.Font(family="Arial", size=10, weight="bold")
        info_frame = ttk.LabelFrame(parent_frame, text="Last Trade Details (This Tick)", padding="5")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)
        last_trade_label = ttk.Label(info_frame, textvariable=self.last_trade_info_var, wraplength=450)
        last_trade_label.grid(row=0, column=0, sticky=tk.W)
        last_trade_reason_label = ttk.Label(info_frame, textvariable=self.last_trade_reason_var)
        last_trade_reason_label.grid(row=1, column=0, sticky=tk.W)

    # --- Helper methods for Treeviews and Recipe ---
    def _create_settlements_treeview(self, parent):
        """Populates the settlements Treeview."""
        # Clear existing items before repopulating
        if hasattr(self, 'settlements_tree'):
            for item in self.settlements_tree.get_children():
                try: self.settlements_tree.delete(item)
                except tk.TclError: pass # Ignore if item already deleted
            # Repopulate with current list of settlements
            for settlement in self.settlements:
                values = [settlement.id, settlement.name, settlement.terrain_type, settlement.population]
                try: self.settlements_tree.insert("", tk.END, iid=settlement.id, values=values)
                except tk.TclError: pass # Ignore if item already exists (shouldn't with clear)

    def _create_goods_treeview(self, parent):
        # (Logic unchanged)
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
        # (Logic unchanged)
        selected_items = self.goods_tree.selection()
        if not selected_items: self._update_recipe_display("(Select a good)"); return
        selected_good = self.world.goods.get(selected_items[0])
        if selected_good and selected_good.recipe:
            recipe = selected_good.recipe; recipe_str = f"** {selected_good.name} ({selected_good.id}) **\n"
            inputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['inputs'].items()]) if recipe['inputs'] else "None"
            recipe_str += f"  Inputs: {inputs_str}\n"
            outputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['outputs'].items()])
            recipe_str += f"  Outputs: {outputs_str}\n"; recipe_str += f"  Labor: {recipe['labor']:.1f}\n"
            if recipe['wealth_cost'] > 0: recipe_str += f"  Wealth Cost: {recipe['wealth_cost']:.1f}\n"
            if recipe['required_terrain']: recipe_str += f"  Requires: {', '.join(recipe['required_terrain'])}\n"
            self._update_recipe_display(recipe_str)
        elif selected_good: self._update_recipe_display(f"** {selected_good.name} ({selected_good.id}) **\n\n(Not producible)")
        else: self._update_recipe_display("(Error: Good not found)")

    def _update_recipe_display(self, text_content):
        # (Logic unchanged)
        self.recipe_text.config(state=tk.NORMAL); self.recipe_text.delete('1.0', tk.END)
        self.recipe_text.insert(tk.END, text_content); self.recipe_text.config(state=tk.DISABLED)

    def _create_dynamic_treeview(self, parent):
        # Populate Treeview with initial data
        if hasattr(self, 'dynamic_tree'):
             for item in self.dynamic_tree.get_children():
                 try: self.dynamic_tree.delete(item)
                 except tk.TclError: pass
             for settlement in self.settlements:
                 storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
                 storage_str = f"{storage_load:.1f}/{storage_cap:.0f}"
                 labor_str = f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}"
                 values = [settlement.name, labor_str, f"{settlement.wealth:.0f}", storage_str]
                 for good in self.sorted_goods:
                     price = settlement.local_prices.get(good.id)
                     stored = settlement.get_total_stored(good.id)
                     values.append(f"{price:.2f}" if price is not None else "N/A")
                     values.append(f"{stored:.1f}" if stored > 1e-6 else "0.0")
                 try: self.dynamic_tree.insert("", tk.END, iid=settlement.id, values=values)
                 except tk.TclError: pass # Ignore if item somehow exists

    # --- Visualization Drawing Methods ---

    def _calculate_settlement_radius(self, wealth):
        # (Using logarithmic formula again)
        try:
            log_input = max(10, wealth)
            radius_increase = math.log10(log_input) * SETTLEMENT_WEALTH_SCALE
        except ValueError: radius_increase = 0
        capped_increase = min(radius_increase, SETTLEMENT_MAX_RADIUS_INCREASE)
        final_radius = SETTLEMENT_BASE_RADIUS + capped_increase
        return final_radius

    def _create_settlement_canvas_items(self):
        """Creates the initial canvas items for ALL current settlements."""
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        self.map_canvas.delete("settlement")
        self.settlement_canvas_items.clear()
        for settlement in self.settlements:
            x, y = settlement.x, settlement.y
            r = SETTLEMENT_BASE_RADIUS
            color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
            circle_id = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
            text_id = self.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=DARK_FG, font=self.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
            wealth_id = self.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=WEALTH_TEXT_COLOR, font=self.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
            self.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
        self._update_settlement_visuals()

    def _update_settlement_visuals(self):
        """Updates the size, color, and text positions of settlements."""
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        for settlement_id, items in self.settlement_canvas_items.items():
            settlement = self.world.settlements.get(settlement_id)
            # Check if settlement exists and all canvas items are present
            if settlement and all(k in items and self.map_canvas.winfo_exists() and items[k] in self.map_canvas.find_all() for k in ['circle', 'text', 'wealth']):
                try:
                    x, y = settlement.x, settlement.y
                    wealth = settlement.wealth
                    new_r = self._calculate_settlement_radius(wealth)
                    circle_id = items['circle']
                    text_id = items['text']
                    wealth_id = items['wealth']
                    current_color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
                    self.map_canvas.coords(circle_id, x - new_r, y - new_r, x + new_r, y + new_r)
                    self.map_canvas.itemconfig(circle_id, fill=current_color) # Update color
                    self.map_canvas.coords(text_id, x, y + new_r + 8)
                    self.map_canvas.coords(wealth_id, x, y - new_r - 8)
                    self.map_canvas.itemconfig(wealth_id, text=f"W: {wealth:.0f}")
                except tk.TclError as e: print(f"WARN: TclError updating visuals for settlement {settlement_id}: {e}")
                except Exception as e: print(f"ERROR updating visuals for settlement {settlement_id}:"); traceback.print_exc()
            elif settlement_id in self.settlement_canvas_items:
                # If settlement exists but items don't, maybe recreate? Or just remove from dict.
                # For now, remove from dict to prevent repeated errors.
                # print(f"WARN: Canvas items missing for settlement {settlement_id}. Removing from tracking.")
                del self.settlement_canvas_items[settlement_id]


    def _draw_trade_route(self, trade_info):
        # (Logic unchanged)
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        seller_id = trade_info['seller_id']; buyer_id = trade_info['buyer_id']
        if seller_id not in self.settlement_coords or buyer_id not in self.settlement_coords: return
        x1, y1 = self.settlement_coords[seller_id]; x2, y2 = self.settlement_coords[buyer_id]
        trade_tag = f"trade_{seller_id}_{buyer_id}_{self.world.tick}_{random.randint(1000,9999)}"
        line_id = self.map_canvas.create_line(x1, y1, x2, y2, fill=TRADE_ROUTE_FLASH_COLOR, width=2.5, arrow=tk.LAST, tags=("trade_route", trade_tag))
        self.root.after(300, lambda lid=line_id: self._set_item_color(lid, TRADE_ROUTE_COLOR))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda lid=line_id: self._delete_canvas_item(lid))
        marker_r = TRADE_MARKER_RADIUS
        dx = x1 - x2; dy = y1 - y2
        dist = max(1, (dx**2 + dy**2)**0.5)
        buyer_settlement = self.world.settlements.get(buyer_id)
        current_buyer_radius = SETTLEMENT_BASE_RADIUS
        if buyer_settlement: current_buyer_radius = self._calculate_settlement_radius(buyer_settlement.wealth)
        offset_scale = current_buyer_radius + marker_r + 2
        marker_x = x2 + (dx / dist) * offset_scale; marker_y = y2 + (dy / dist) * offset_scale
        marker_id = self.map_canvas.create_oval(marker_x - marker_r, marker_y - marker_r, marker_x + marker_r, marker_y + marker_r, fill=TRADE_MARKER_COLOR, outline="", tags=("trade_marker", trade_tag))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda mid=marker_id: self._delete_canvas_item(mid))

    def _set_item_color(self, item_id, color):
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists(): self.map_canvas.itemconfig(item_id, fill=color)
        except tk.TclError: pass

    def _delete_canvas_item(self, item_id):
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists(): self.map_canvas.delete(item_id)
        except tk.TclError: pass

    # --- Main Update Loop ---
    def update_simulation(self):
        if not self.root.winfo_exists(): print("Root window closed, stopping simulation loop."); return
        try:
            # 1. Run simulation step
            self.world.simulation_step()

            # 2. Update Tick Label
            self.tick_label_var.set(f"Tick: {self.world.tick}")

            # 3. Update Dynamic Treeview Table
            # Ensure self.settlements reflects the current state from self.world
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            current_tree_items = set(self.dynamic_tree.get_children())
            settlement_ids_in_world = set(s.id for s in self.settlements)

            # Update existing/add new items
            for settlement in self.settlements:
                storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
                storage_str = f"{storage_load:.1f}/{storage_cap:.0f}"
                labor_str = f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}"
                values = [settlement.name, labor_str, f"{settlement.wealth:.0f}", storage_str]
                for good in self.sorted_goods:
                    price = settlement.local_prices.get(good.id)
                    stored = settlement.get_total_stored(good.id)
                    values.append(f"{price:.2f}" if price is not None else "N/A")
                    values.append(f"{stored:.1f}" if stored > 1e-6 else "0.0")

                if settlement.id in current_tree_items:
                    try: self.dynamic_tree.item(settlement.id, values=values)
                    except tk.TclError: pass # Item might have been deleted if treeview cleared
                else: # Insert new settlement row
                    try: self.dynamic_tree.insert("", tk.END, iid=settlement.id, values=values)
                    except tk.TclError: pass # Item might already exist if there's a race condition

            # Remove rows for settlements that no longer exist (if dynamic removal implemented later)
            ids_to_remove_from_tree = current_tree_items - settlement_ids_in_world
            for item_id in ids_to_remove_from_tree:
                try: self.dynamic_tree.delete(item_id)
                except tk.TclError: pass


            # 4. Update Trade Log (Text)
            self.trade_log_text.config(state=tk.NORMAL); self.trade_log_text.delete('1.0', tk.END)
            log_content = "\n".join(self.world.recent_trades_log) if self.world.recent_trades_log else "- No trades yet -"
            self.trade_log_text.insert(tk.END, log_content); self.trade_log_text.config(state=tk.DISABLED)
            self.trade_log_text.yview_moveto(1.0)

            # 5. Update Visualization Canvas & Info
            last_trade_details = None
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists():
                # Ensure canvas items exist for all current settlements before updating
                current_canvas_settlement_ids = set(self.settlement_canvas_items.keys())
                settlement_ids_in_world = set(s.id for s in self.settlements)
                new_settlement_ids = settlement_ids_in_world - current_canvas_settlement_ids
                removed_settlement_ids = current_canvas_settlement_ids - settlement_ids_in_world

                # Add items for new settlements (if dynamic addition were implemented)
                # for new_id in new_settlement_ids: self._create_single_settlement_item(self.world.settlements[new_id])

                # Remove items for deleted settlements (if dynamic removal were implemented)
                # for removed_id in removed_settlement_ids: self._remove_single_settlement_item(removed_id)

                # Update visuals for all existing settlements
                self._update_settlement_visuals()

                # Draw trade routes/markers for this tick
                trades_this_tick = list(self.world.executed_trade_details_this_tick)
                if trades_this_tick:
                    for trade_info in trades_this_tick:
                         self._draw_trade_route(trade_info)
                         last_trade_details = trade_info
                else:
                     self.last_trade_info_var.set("No trades this tick.")
                     self.last_trade_reason_var.set("")

            # Update the info display labels
            if last_trade_details:
                info_text = (f"Trade: {last_trade_details['quantity']:.1f} {last_trade_details['good_name']} "
                             f"from {last_trade_details['seller_name']} to {last_trade_details['buyer_name']}")
                reason_text = (f"Reason: Seller Price={last_trade_details['seller_price']:.2f}, "
                               f"Buyer Price={last_trade_details['buyer_price']:.2f} "
                               f"(Profit/Unit={last_trade_details['profit_per_unit']:.2f})")
                self.last_trade_info_var.set(info_text)
                self.last_trade_reason_var.set(reason_text)

            # 6. Schedule the next update
            self.root.after(TICK_DELAY_MS, self.update_simulation)

        except Exception as e:
            print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---");
            traceback.print_exc(); # Print full traceback
            if self.root.winfo_exists(): self.root.quit()

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    try: app = SimulationUI(root); root.mainloop()
    except Exception as e: print(f"\n--- FATAL ERROR INITIALIZING UI ---"); traceback.print_exc();
    finally: print("UI Closed / Application Finished.")

