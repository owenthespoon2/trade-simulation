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
from collections import Counter # Needed for migration summary (optional)

# ==============================================================================
# FILE INDEX
# ==============================================================================
# - Imports & Theme Setup                 : Line 1
# - Load UI/Sim Configuration             : Line 23
# - UI Constants                          : Line 48
# - SimulationUI Class                    : Line 62
#   - __init__                            : Line 63
#   - Control Methods (_pause_sim, etc.)  : Line 99
#   - Theme Application (_apply_theme)    : Line 108
#   - UI Setup Methods
#     - _setup_static_pane                : Line 121
#     - _setup_notebook                   : Line 146
#     - _setup_dynamic_widgets            : Line 154
#     - _setup_visualization_widgets      : Line 172
#   - Treeview Creation/Update Methods
#     - _create_settlements_treeview      : Line 181
#     - _create_goods_treeview            : Line 189
#     - _on_good_select                   : Line 197
#     - _update_recipe_display            : Line 207
#     - _create_dynamic_treeview          : Line 209
#   - Visualization Drawing Methods
#     - _calculate_settlement_radius      : Line 220
#     - _create_settlement_canvas_items   : Line 229
#     - _update_settlement_visuals        : Line 241
#     - _create_single_settlement_item    : Line 263
#     - _draw_trade_route                 : Line 271
#     - _set_item_color / _delete_canvas_item : Line 285
#   - Trade Analysis Window Methods
#     - _open_trade_analysis_window       : Line 294
#     - _create_analysis_treeview         : Line 326
#     - _sort_treeview_column             : Line 340
#     - _safe_format_float                : Line 348
#     - _update_trade_analysis_window     : Line 358
#     - _on_analysis_window_close         : Line 406
#   - Main Update Loop (update_simulation): Line 411
# - Main Execution Block                  : Line 456
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
    # Ensure we import the updated logic classes
    from trade_logic import World, Good, Settlement, ItemInstance
except ImportError:
    print("ERROR: Make sure 'trade_logic.py' exists and is runnable.")
    sys.exit(1)
try:
    from world_setup import setup_world
except ImportError:
    print("ERROR: Make sure 'world_setup.py' exists and is runnable.")
    sys.exit(1)

# --- Load UI Configuration ---
# Default values in case config.json is missing or incomplete
DEFAULT_UI_PARAMS = {
    "tick_delay_ms": 1000, "trade_effect_duration_ms": 1200,
    "settlement_radius": 15, "trade_marker_radius": 4,
    "window_title": "Emergent Trade Simulation", "settlement_base_radius": 8,
    "settlement_wealth_scale": 4.0, # Kept for potential fallback if needed
    "settlement_wealth_sqrt_scale": 0.5, # Used for sqrt scaling of radius
    "settlement_max_radius_increase": 25,
    "city_color": "#e27a7a"
}
DEFAULT_SIM_PARAMS = { "city_population_threshold": 150 } # Default needed by UI

# Load parameters from config.json, merging with defaults
ui_params = DEFAULT_UI_PARAMS.copy()
sim_params_for_ui = DEFAULT_SIM_PARAMS.copy() # Only load sim params needed by UI
try:
    with open("config.json", 'r') as f:
        config_data = json.load(f)
        loaded_ui_params = config_data.get("ui_parameters", {})
        loaded_sim_params = config_data.get("simulation_parameters", {})
        ui_params.update(loaded_ui_params) # Overwrite defaults with loaded values
        # Specifically get city threshold needed for coloring settlements
        sim_params_for_ui['city_population_threshold'] = loaded_sim_params.get(
            'city_population_threshold', DEFAULT_SIM_PARAMS['city_population_threshold']
        )
    print(f"Loaded UI parameters from config.json: {ui_params}")
except FileNotFoundError:
    print("WARN: config.json not found. Using default UI parameters.")
except json.JSONDecodeError:
    print("ERROR: Could not decode config.json. Using default UI parameters.")
except Exception as e:
    print(f"ERROR loading UI parameters from config.json: {e}. Using defaults.")

# --- UI Constants ---
# Set constants from the loaded (or default) parameters
TICK_DELAY_MS = ui_params['tick_delay_ms']
WINDOW_TITLE = ui_params['window_title']
TRADE_EFFECT_DURATION_MS = ui_params['trade_effect_duration_ms']
SETTLEMENT_BASE_RADIUS = ui_params['settlement_base_radius']
SETTLEMENT_WEALTH_SCALE_PARAM = ui_params.get('settlement_wealth_sqrt_scale', 0.5) # Use sqrt scale
SETTLEMENT_MAX_RADIUS_INCREASE = ui_params['settlement_max_radius_increase']
TRADE_MARKER_RADIUS = ui_params['trade_marker_radius']
CITY_COLOR = ui_params.get('city_color', "#e27a7a")
CITY_POP_THRESHOLD = sim_params_for_ui['city_population_threshold'] # Get threshold from loaded params

# Theme colors (used if sv_ttk is not available or for specific elements)
DARK_BG = "#2e2e2e"
DARK_FG = "#cccccc"
DARK_INSERT_BG = "#555555"
CANVAS_BG = "#1e1e1e"
SETTLEMENT_COLOR = "#4a90e2"
WEALTH_TEXT_COLOR = "#ffffff"
TRADE_ROUTE_COLOR = "#f5a623"
TRADE_ROUTE_FLASH_COLOR = "#ffffff"
TRADE_MARKER_COLOR = "#50e3c2"

# --- Main Simulation UI Class ---
class SimulationUI:
    """Manages the Tkinter user interface for the trade simulation."""

    def __init__(self, root):
        """Initializes the UI, sets up the world, and creates widgets."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        try:
            # Attempt to maximize the window
            self.root.state('zoomed')
        except tk.TclError:
            print("WARN: Could not zoom window (may not be supported on this OS/WM).")

        # Apply dark theme if available
        self._apply_theme()

        self.simulation_running = True # Controls the main update loop

        # References for the analysis window and its treeviews
        self.analysis_window = None
        self.analysis_tree_potential = None
        self.analysis_tree_failed = None
        self.analysis_tree_executed = None
        self.analysis_tree_migration = None # <<< Added for migration tab

        print("Setting up world...")
        try:
            # Initialize the simulation world using the setup function
            self.world = setup_world(config_file="config.json", recipe_file="recipes.json")
            # Get initial data for UI display
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            # Store settlement coordinates (including z, though not used for drawing yet)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            # Dictionary to store canvas item IDs for each settlement
            self.settlement_canvas_items = {}
            print("World setup complete.")
        except Exception as e:
            # Handle critical errors during world setup
            print(f"\n--- ERROR DURING WORLD SETUP ---")
            print(e)
            traceback.print_exc()
            self.root.quit()
            return

        # Tkinter variables for dynamic labels
        self.last_trade_info_var = tk.StringVar(value="No trades yet this tick.")
        self.last_trade_reason_var = tk.StringVar(value="")
        self.tick_label_var = tk.StringVar(value="Tick: 0")

        # --- Create Main UI Frames ---
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Configure resizing behavior
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        # Configure main frame columns (static pane on left, notebook on right)
        self.main_frame.columnconfigure(0, weight=1, minsize=300) # Static pane width
        self.main_frame.columnconfigure(1, weight=4, minsize=600) # Notebook width
        self.main_frame.rowconfigure(1, weight=1) # Allow main content row to expand

        # --- Control Bar ---
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        self.tick_label = ttk.Label(control_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        self.tick_label.pack(side=tk.LEFT, padx=(0, 20))
        # Start/Pause buttons
        self.start_button = ttk.Button(control_frame, text="Start", command=self._start_sim, state=tk.DISABLED)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self._pause_sim, state=tk.NORMAL)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        # Button to open analysis window
        analysis_button = ttk.Button(control_frame, text="Trade Analysis", command=self._open_trade_analysis_window)
        analysis_button.pack(side=tk.LEFT, padx=5)

        # --- Setup Main Content Areas ---
        self._setup_static_pane() # Left pane with static info (settlements, goods)
        self._setup_notebook()    # Right pane with tabs (tables, map)

        print("Starting simulation loop...")
        try:
             # Initial drawing of settlements on the map
             self._create_settlement_canvas_items()
             # Schedule the first call to the main update loop
             if self.simulation_running:
                 self.root.after(TICK_DELAY_MS, self.update_simulation)
        except Exception as e:
             # Handle errors during initial UI setup/drawing
             print(f"\n--- ERROR ON FIRST SIMULATION START ---")
             print(e)
             traceback.print_exc()
             self.root.quit()

    # --- Simulation Control Methods ---
    def _pause_sim(self):
        """Pauses the simulation update loop."""
        if self.simulation_running:
            self.simulation_running = False
            self.pause_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            print("--- Simulation Paused ---")

    def _start_sim(self):
        """Resumes the simulation update loop."""
        if not self.simulation_running:
            self.simulation_running = True
            self.pause_button.config(state=tk.NORMAL)
            self.start_button.config(state=tk.DISABLED)
            print("--- Simulation Resumed ---")
            # Immediately schedule the next update
            self.root.after(10, self.update_simulation)

    # --- Theme Application ---
    def _apply_theme(self):
        """Applies the sv_ttk dark theme if available, otherwise uses fallback styling."""
        if SV_TTK_AVAILABLE:
            sv_ttk.set_theme("dark")
            self.root.configure(bg=DARK_BG) # Ensure root background matches
        else:
             # Basic fallback dark theme using standard ttk styles
             print("Applying basic fallback dark theme...")
             style = ttk.Style()
             # Try 'clam' theme first, fallback to 'alt'
             theme_to_use = 'clam' if 'clam' in style.theme_names() else 'alt'
             try:
                 style.theme_use(theme_to_use)
             except tk.TclError:
                 print(f"WARN: Could not use theme '{theme_to_use}'. Using default.")

             self.root.config(bg=DARK_BG) # Set root background
             # Configure default style for all widgets
             style.configure('.', background=DARK_BG, foreground=DARK_FG)
             style.configure('TFrame', background=DARK_BG)
             style.configure('TLabel', background=DARK_BG, foreground=DARK_FG)
             style.configure('TLabelFrame', background=DARK_BG, foreground=DARK_FG)
             style.configure('TLabelFrame.Label', background=DARK_BG, foreground=DARK_FG)
             # Style Treeview specifically
             style.configure('Treeview', background="#3f3f3f", foreground=DARK_FG, fieldbackground="#3f3f3f")
             style.configure('Treeview.Heading', background="#4a4a4a", foreground=DARK_FG)
             style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
             # Style Scrollbar
             style.configure('TScrollbar', background=DARK_BG, troughcolor="#4a4a4a")
             # Style Notebook tabs
             style.configure("TNotebook", background=DARK_BG, borderwidth=0)
             style.configure("TNotebook.Tab", background="#4a4a4a", foreground=DARK_FG, padding=[5, 2], borderwidth=0)
             style.map("TNotebook.Tab", background=[("selected", SETTLEMENT_COLOR)], foreground=[("selected", "white")])

    # --- UI Setup Methods ---
    def _setup_static_pane(self):
        """Sets up the left pane containing static information."""
        static_pane = ttk.Frame(self.main_frame, padding="5")
        static_pane.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        # Configure row weights for vertical expansion
        static_pane.rowconfigure(1, weight=1) # Settlements treeview
        static_pane.rowconfigure(3, weight=1) # Goods treeview
        static_pane.rowconfigure(5, weight=2) # Recipe text area
        static_pane.columnconfigure(0, weight=1) # Allow content to expand horizontally

        # --- Settlements List ---
        ttk.Label(static_pane, text="Settlements", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        columns = ["id", "name", "terrain", "pop"]
        column_names = ["ID", "Name", "Terrain", "Pop"]
        self.settlements_tree = ttk.Treeview(static_pane, columns=columns, show="headings", height=8)
        for col, name in zip(columns, column_names):
            self.settlements_tree.heading(col, text=name)
            # Set column widths and alignment
            width = 100; anchor = tk.W
            if col == "id": width = 30
            elif col == "pop": width = 60; anchor = tk.E
            self.settlements_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self._create_settlements_treeview(static_pane) # Populate the treeview
        self.settlements_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Scrollbar for settlements tree
        settlements_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.settlements_tree.yview)
        self.settlements_tree.configure(yscrollcommand=settlements_scrollbar.set)
        settlements_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # --- Goods List ---
        ttk.Label(static_pane, text="Goods", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self._create_goods_treeview(static_pane) # Create and populate the goods treeview
        self.goods_tree.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Scrollbar for goods tree
        goods_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.goods_tree.yview)
        self.goods_tree.configure(yscrollcommand=goods_scrollbar.set)
        goods_scrollbar.grid(row=3, column=1, sticky=(tk.N, tk.S))
        # Bind selection event to update recipe display
        self.goods_tree.bind("<<TreeviewSelect>>", self._on_good_select)

        # --- Recipe Details ---
        ttk.Label(static_pane, text="Recipe Details", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.recipe_text = tk.Text(static_pane, wrap=tk.WORD, state=tk.DISABLED, height=10,
                                   bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG,
                                   borderwidth=1, relief=tk.SUNKEN)
        recipe_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.recipe_text.yview)
        self.recipe_text.config(yscrollcommand=recipe_scrollbar.set)
        self.recipe_text.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        recipe_scrollbar.grid(row=5, column=1, sticky=(tk.N, tk.S))
        self._update_recipe_display("(Select a good)") # Initial placeholder text

    def _setup_notebook(self):
        """Sets up the right pane with tabs for dynamic data and visualization."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5,0))

        # --- Tables Tab ---
        self.dynamic_pane = ttk.Frame(self.notebook, padding="5")
        self.dynamic_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Configure resizing
        self.dynamic_pane.rowconfigure(1, weight=3) # Settlement state table
        self.dynamic_pane.rowconfigure(4, weight=1) # Trade log
        self.dynamic_pane.columnconfigure(0, weight=1)
        self._setup_dynamic_widgets(self.dynamic_pane) # Add widgets to this tab

        # --- Map Tab ---
        self.viz_pane = ttk.Frame(self.notebook, padding="5")
        self.viz_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Configure resizing
        self.viz_pane.rowconfigure(1, weight=1) # Map canvas
        self.viz_pane.rowconfigure(2, weight=0) # Info frame (fixed size)
        self.viz_pane.columnconfigure(0, weight=1)
        self._setup_visualization_widgets(self.viz_pane) # Add widgets to this tab

        # Add tabs to the notebook
        self.notebook.add(self.dynamic_pane, text='Tables')
        self.notebook.add(self.viz_pane, text='Map')

    def _setup_dynamic_widgets(self, parent_frame):
        """Sets up widgets for the 'Tables' tab (dynamic settlement state, trade log)."""
        # --- Settlement State Table ---
        ttk.Label(parent_frame, text="Settlement State", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        # Define columns dynamically based on loaded goods
        columns = ["name", "labor", "wealth", "storage"]
        column_names = ["Settlement", "Labor", "Wealth", "Storage"]
        for good in self.sorted_goods:
            columns.append(f"{good.id}_price")
            column_names.append(f"{good.name} Prc") # Price column
            columns.append(f"{good.id}_stored")
            column_names.append(f"{good.name} Stk") # Stock column
        self.dynamic_tree = ttk.Treeview(parent_frame, columns=columns, show="headings")
        # Configure column headings, widths, and alignment
        for col, name in zip(columns, column_names):
            self.dynamic_tree.heading(col, text=name)
            width = 70; anchor = tk.E # Default right-align for numbers
            if col == "name": width = 90; anchor = tk.W
            elif col == "labor": width = 80
            elif col == "storage": width = 80
            self.dynamic_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        self._create_dynamic_treeview(parent_frame) # Populate the treeview
        self.dynamic_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Scrollbars for dynamic state tree
        dynamic_scrollbar_y = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.dynamic_tree.yview)
        dynamic_scrollbar_x = ttk.Scrollbar(parent_frame, orient=tk.HORIZONTAL, command=self.dynamic_tree.xview)
        self.dynamic_tree.configure(yscrollcommand=dynamic_scrollbar_y.set, xscrollcommand=dynamic_scrollbar_x.set)
        dynamic_scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        dynamic_scrollbar_x.grid(row=2, column=0, sticky=(tk.W, tk.E))

        # --- Recent Trades Log ---
        ttk.Label(parent_frame, text="Recent Trades Log", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.trade_log_text = tk.Text(parent_frame, height=8, width=80, wrap=tk.WORD, state=tk.DISABLED,
                                      bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG,
                                      borderwidth=1, relief=tk.SUNKEN )
        trade_log_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.trade_log_text.yview)
        self.trade_log_text.config(yscrollcommand=trade_log_scrollbar.set)
        self.trade_log_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        trade_log_scrollbar.grid(row=4, column=1, sticky=(tk.N, tk.S))

    def _setup_visualization_widgets(self, parent_frame):
        """Sets up widgets for the 'Map' tab (canvas, info labels)."""
        # --- Map Canvas ---
        ttk.Label(parent_frame, text="Trade Map", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.map_canvas = tk.Canvas(parent_frame, bg=CANVAS_BG, width=500, height=400, highlightthickness=0)
        self.map_canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Define fonts used on the canvas
        self.settlement_font = tkFont.Font(family="Arial", size=9)
        self.wealth_font = tkFont.Font(family="Arial", size=10, weight="bold")
        # FUTURE: Replace simple canvas map with a more advanced rendering solution.

        # --- Info Frame (Below Map) ---
        info_frame = ttk.LabelFrame(parent_frame, text="Last Trade Details (This Tick)", padding="5")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        info_frame.columnconfigure(0, weight=1) # Allow label to expand horizontally
        # Labels to display details of the most recent trade event
        last_trade_label = ttk.Label(info_frame, textvariable=self.last_trade_info_var, wraplength=450)
        last_trade_label.grid(row=0, column=0, sticky=tk.W)
        last_trade_reason_label = ttk.Label(info_frame, textvariable=self.last_trade_reason_var)
        last_trade_reason_label.grid(row=1, column=0, sticky=tk.W)

    # --- Treeview Creation/Update Methods ---
    def _create_settlements_treeview(self, parent):
        """Creates and populates the static settlements list treeview."""
        if hasattr(self, 'settlements_tree'):
            # Clear existing items before repopulating (useful if settlements could change)
            for item in self.settlements_tree.get_children():
                try: self.settlements_tree.delete(item)
                except tk.TclError: pass # Ignore error if item already deleted
            # Insert data for each settlement
            for settlement in self.settlements:
                values = [settlement.id, settlement.name, settlement.terrain_type, settlement.population]
                try: self.settlements_tree.insert("", tk.END, iid=settlement.id, values=values)
                except tk.TclError: pass # Ignore error if item ID already exists (shouldn't happen here)

    def _create_goods_treeview(self, parent):
        """Creates and populates the static goods list treeview."""
        columns = ["id", "name", "base_value", "producible"]
        column_names = ["ID", "Name", "Base Val", "Prod?"]
        self.goods_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        for col, name in zip(columns, column_names):
            self.goods_tree.heading(col, text=name)
            width = 80; anchor = tk.W
            if col == "base_value": anchor = tk.E # Right-align value
            self.goods_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        # Insert data for each good
        for good in self.sorted_goods:
            values = [good.id, good.name, f"{good.base_value:.1f}", "Yes" if good.is_producible else "No"]
            self.goods_tree.insert("", tk.END, iid=good.id, values=values)

    def _on_good_select(self, event):
        """Callback function when a good is selected in the goods_tree."""
        selected_items = self.goods_tree.selection()
        if not selected_items:
            self._update_recipe_display("(Select a good)")
            return
        # Get the Good object corresponding to the selected item ID
        selected_good = self.world.goods.get(selected_items[0])
        if selected_good and selected_good.recipe:
            # Format and display the recipe if it exists
            recipe = selected_good.recipe
            recipe_str = f"** {selected_good.name} ({selected_good.id}) **\n"
            inputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['inputs'].items()]) if recipe['inputs'] else "None"
            recipe_str += f"  Inputs: {inputs_str}\n"
            outputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['outputs'].items()])
            recipe_str += f"  Outputs: {outputs_str}\n"
            recipe_str += f"  Labor: {recipe['labor']:.1f}\n"
            if recipe['wealth_cost'] > 0: recipe_str += f"  Wealth Cost: {recipe['wealth_cost']:.1f}\n"
            if recipe['required_terrain']: recipe_str += f"  Requires: {', '.join(recipe['required_terrain'])}\n"
            self._update_recipe_display(recipe_str)
        elif selected_good:
            # Display message if the good is not producible
            self._update_recipe_display(f"** {selected_good.name} ({selected_good.id}) **\n\n(Not producible)")
        else:
            # Handle error case where selected good ID is not found
            self._update_recipe_display("(Error: Good not found)")

    def _update_recipe_display(self, text_content):
        """Updates the content of the recipe details text area."""
        self.recipe_text.config(state=tk.NORMAL) # Enable editing
        self.recipe_text.delete('1.0', tk.END)   # Clear existing content
        self.recipe_text.insert(tk.END, text_content) # Insert new content
        self.recipe_text.config(state=tk.DISABLED) # Disable editing

    def _create_dynamic_treeview(self, parent):
        """Creates and populates the dynamic settlement state treeview."""
        # FUTURE: UI will need drill-down capabilities to show internal settlement details.
        if hasattr(self, 'dynamic_tree'):
             # Clear existing items
             for item in self.dynamic_tree.get_children():
                 try: self.dynamic_tree.delete(item)
                 except tk.TclError: pass
             # Insert current data for each settlement
             for settlement in self.settlements:
                 # Format storage and labor strings
                 storage_load = settlement.get_current_storage_load()
                 storage_cap = settlement.storage_capacity
                 storage_str = f"{storage_load:.1f}/{storage_cap:.0f}"
                 labor_str = f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}"
                 # Basic settlement info
                 values = [settlement.name, labor_str, f"{settlement.wealth:.0f}", storage_str]
                 # Add price and stock for each good dynamically
                 for good in self.sorted_goods:
                     price = settlement.local_prices.get(good.id)
                     stored = settlement.get_total_stored(good.id)
                     values.append(f"{price:.2f}" if price is not None else "N/A")
                     values.append(f"{stored:.1f}" if stored > 1e-6 else "0.0")
                 # Insert the row into the treeview
                 try: self.dynamic_tree.insert("", tk.END, iid=settlement.id, values=values)
                 except tk.TclError: pass # Ignore if ID somehow exists

    # --- Visualization Drawing Methods ---
    def _calculate_settlement_radius(self, wealth):
        """Calculates settlement radius for map visualization based on wealth using sqrt scale."""
        try:
            # Use square root for potentially more pronounced visual difference than log
            # Ensure non-negative input to sqrt
            radius_increase = math.sqrt(max(0, wealth)) * SETTLEMENT_WEALTH_SCALE_PARAM
        except ValueError:
             # Handle potential math errors (though max(0, wealth) should prevent domain errors)
            radius_increase = 0
        # Cap the increase to prevent excessively large circles
        capped_increase = min(radius_increase, SETTLEMENT_MAX_RADIUS_INCREASE)
        # Final radius is base + calculated increase
        final_radius = SETTLEMENT_BASE_RADIUS + capped_increase
        return final_radius

    def _create_settlement_canvas_items(self):
        """Creates the initial visual representation of settlements on the map canvas."""
        # Check if canvas exists and is valid
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        # Clear any previous settlement items
        self.map_canvas.delete("settlement")
        self.settlement_canvas_items.clear()
        # Create items for each settlement
        for settlement in self.settlements:
            # Get coordinates (ignore z for 2D canvas)
            x, y, _ = self.settlement_coords[settlement.id]
            r = SETTLEMENT_BASE_RADIUS # Initial radius
            # Determine color based on city status
            color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
            # Create circle, name text, and wealth text
            # Store the IDs of the created canvas items for later updates
            # FUTURE: Z coordinate exists (settlement.z) but is not used for visualization here.
            circle_id = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
            text_id = self.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=DARK_FG, font=self.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
            wealth_id = self.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=WEALTH_TEXT_COLOR, font=self.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
            self.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
        # Apply initial scaling based on wealth
        self._update_settlement_visuals()

    def _update_settlement_visuals(self):
        """Updates the size, color, and text of settlement representations on the map."""
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return

        # --- Handle Removed Settlements ---
        # Get IDs of settlements currently in the simulation logic
        valid_settlement_ids = set(s.id for s in self.settlements)
        # Find IDs of canvas items whose corresponding settlement no longer exists
        ids_to_remove_from_canvas = set(self.settlement_canvas_items.keys()) - valid_settlement_ids
        # Remove canvas items associated with removed settlements
        for settlement_id in ids_to_remove_from_canvas:
            if settlement_id in self.settlement_canvas_items:
                items = self.settlement_canvas_items[settlement_id]
                for item_key in ['circle', 'text', 'wealth']:
                     if item_key in items: self._delete_canvas_item(items[item_key])
                del self.settlement_canvas_items[settlement_id] # Remove from tracking dict

        # --- Update Existing/Add New Settlements ---
        for settlement in self.settlements:
            settlement_id = settlement.id
            items = self.settlement_canvas_items.get(settlement_id)

            # Check if canvas items exist and are valid
            items_valid = items and all(k in items and self.map_canvas.winfo_exists() and items[k] in self.map_canvas.find_all() for k in ['circle', 'text', 'wealth'])

            if items_valid:
                # Update existing items
                try:
                    # Get current coordinates (ignore z) and wealth
                    x, y, _ = self.settlement_coords[settlement.id]
                    wealth = settlement.wealth
                    new_r = self._calculate_settlement_radius(wealth) # Calculate new radius
                    circle_id = items['circle']
                    text_id = items['text']
                    wealth_id = items['wealth']
                    # Update color based on city status
                    current_color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
                    # Update circle position/size and color
                    self.map_canvas.coords(circle_id, x - new_r, y - new_r, x + new_r, y + new_r)
                    self.map_canvas.itemconfig(circle_id, fill=current_color)
                    # Update text positions based on new radius
                    self.map_canvas.coords(text_id, x, y + new_r + 8)
                    self.map_canvas.coords(wealth_id, x, y - new_r - 8)
                    # Update wealth text content
                    self.map_canvas.itemconfig(wealth_id, text=f"W: {wealth:.0f}")
                except tk.TclError as e:
                    # Catch potential errors if canvas items become invalid during update
                    print(f"WARN: TclError updating visuals for settlement {settlement_id}: {e}")
                except Exception as e:
                    # Catch other unexpected errors
                    print(f"ERROR updating visuals for settlement {settlement_id}:")
                    traceback.print_exc()
            elif settlement_id not in self.settlement_canvas_items:
                 # If settlement exists in logic but not on canvas, create its items
                 self._create_single_settlement_item(settlement)

    def _create_single_settlement_item(self, settlement):
        """Creates canvas items for a single new settlement (e.g., if added mid-simulation)."""
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return
        # Avoid creating duplicates if called unnecessarily
        if settlement.id in self.settlement_canvas_items: return

        # Get coordinates (ignore z)
        x, y, _ = self.settlement_coords[settlement.id]
        r = SETTLEMENT_BASE_RADIUS # Initial radius
        # Determine color
        color = CITY_COLOR if settlement.population >= CITY_POP_THRESHOLD else SETTLEMENT_COLOR
        # Create canvas items
        circle_id = self.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
        text_id = self.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=DARK_FG, font=self.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
        wealth_id = self.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=WEALTH_TEXT_COLOR, font=self.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
        # Store item IDs
        self.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
        # Immediately update size based on current wealth
        self._update_settlement_visuals() # Call update to set correct radius immediately

    def _draw_trade_route(self, trade_info):
        """Draws a temporary line and marker on the map to visualize a trade."""
        if not hasattr(self, 'map_canvas') or not self.map_canvas.winfo_exists(): return

        seller_id = trade_info['seller_id']
        buyer_id = trade_info['buyer_id']

        # Ensure coordinates exist for both settlements
        if seller_id not in self.settlement_coords or buyer_id not in self.settlement_coords: return

        # Get coordinates (ignore z for drawing)
        x1, y1, _ = self.settlement_coords[seller_id]
        x2, y2, _ = self.settlement_coords[buyer_id]

        # Create unique tag for this specific trade effect instance
        trade_tag = f"trade_{seller_id}_{buyer_id}_{self.world.tick}_{random.randint(1000,9999)}"

        # Draw the flashing line (starts white, fades to orange)
        line_id = self.map_canvas.create_line(x1, y1, x2, y2, fill=TRADE_ROUTE_FLASH_COLOR, width=2.5, arrow=tk.LAST, tags=("trade_route", trade_tag))
        # Schedule color change and deletion
        self.root.after(300, lambda lid=line_id: self._set_item_color(lid, TRADE_ROUTE_COLOR))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda lid=line_id: self._delete_canvas_item(lid))

        # Draw the temporary marker near the buyer
        marker_r = TRADE_MARKER_RADIUS
        dx = x1 - x2; dy = y1 - y2
        dist = max(1, (dx**2 + dy**2)**0.5) # Avoid division by zero

        # Calculate offset based on buyer's current radius
        buyer_settlement = self.world.settlements.get(buyer_id)
        current_buyer_radius = SETTLEMENT_BASE_RADIUS # Default if buyer not found (shouldn't happen)
        if buyer_settlement:
            current_buyer_radius = self._calculate_settlement_radius(buyer_settlement.wealth)

        # Position marker just outside the buyer's circle edge
        offset_scale = current_buyer_radius + marker_r + 2 # Small gap
        marker_x = x2 + (dx / dist) * offset_scale
        marker_y = y2 + (dy / dist) * offset_scale

        # Create marker and schedule its deletion
        marker_id = self.map_canvas.create_oval(marker_x - marker_r, marker_y - marker_r, marker_x + marker_r, marker_y + marker_r, fill=TRADE_MARKER_COLOR, outline="", tags=("trade_marker", trade_tag))
        self.root.after(TRADE_EFFECT_DURATION_MS, lambda mid=marker_id: self._delete_canvas_item(mid))

    def _set_item_color(self, item_id, color):
        """Safely changes the fill color of a canvas item."""
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists():
                self.map_canvas.itemconfig(item_id, fill=color)
        except tk.TclError:
            pass # Ignore error if item no longer exists

    def _delete_canvas_item(self, item_id):
        """Safely deletes a canvas item."""
        try:
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists():
                self.map_canvas.delete(item_id)
        except tk.TclError:
            pass # Ignore error if item no longer exists

    # --- Trade Analysis Window ---
    def _open_trade_analysis_window(self):
        """Opens or focuses the trade analysis window."""
        # If window already exists, bring it to the front
        if self.analysis_window and self.analysis_window.winfo_exists():
            self.analysis_window.lift()
            return

        # Create new top-level window
        self.analysis_window = tk.Toplevel(self.root)
        self.analysis_window.title(f"Trade & Migration Analysis (Tick {self.world.tick})") # Updated title
        self.analysis_window.geometry("1000x700") # Set initial size

        # Apply theme if available
        try:
            if SV_TTK_AVAILABLE:
                 sv_ttk.set_theme("dark")
                 self.analysis_window.configure(bg=DARK_BG)
        except Exception as e:
            print(f"WARN: Could not apply theme to analysis window: {e}")

        # Configure resizing
        self.analysis_window.rowconfigure(0, weight=1)
        self.analysis_window.columnconfigure(0, weight=1)

        # Create notebook for tabs
        notebook = ttk.Notebook(self.analysis_window)
        notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # --- Define Tabs and Columns ---
        # Executed Trades Tab
        exec_frame = ttk.Frame(notebook, padding=5)
        notebook.add(exec_frame, text="Executed Trades")
        exec_frame.rowconfigure(0, weight=1); exec_frame.columnconfigure(0, weight=1)
        exec_cols = ('From', 'To', 'Good', 'Qty', 'Sell P', 'Buy P', 'Profit/U', 'Total Val')
        self.analysis_tree_executed = self._create_analysis_treeview(exec_frame, exec_cols)

        # Failed Trades Tab
        fail_frame = ttk.Frame(notebook, padding=5)
        notebook.add(fail_frame, text="Failed Executions")
        fail_frame.rowconfigure(0, weight=1); fail_frame.columnconfigure(0, weight=1)
        fail_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Reason')
        self.analysis_tree_failed = self._create_analysis_treeview(fail_frame, fail_cols)

        # Potential Trades Tab
        pot_frame = ttk.Frame(notebook, padding=5)
        notebook.add(pot_frame, text="Viable Potential Trades")
        pot_frame.rowconfigure(0, weight=1); pot_frame.columnconfigure(0, weight=1)
        pot_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q')
        self.analysis_tree_potential = self._create_analysis_treeview(pot_frame, pot_cols)

        # <<< Migration Tab >>>
        mig_frame = ttk.Frame(notebook, padding=5)
        notebook.add(mig_frame, text="Migration") # Add the new tab
        mig_frame.rowconfigure(0, weight=1); mig_frame.columnconfigure(0, weight=1)
        mig_cols = ('Tick', 'From', 'To', 'Quantity') # Define columns
        # Create the treeview for this tab
        self.analysis_tree_migration = self._create_analysis_treeview(mig_frame, mig_cols)

        # Populate the window with current data
        self._update_trade_analysis_window()

        # Set cleanup action when window is closed
        self.analysis_window.protocol("WM_DELETE_WINDOW", self._on_analysis_window_close)

    def _create_analysis_treeview(self, parent, columns):
        """Helper function to create a Treeview with scrollbars within a parent frame."""
        frame = ttk.Frame(parent)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.grid(row=0, column=0, sticky="nsew")

        # Vertical scrollbar
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        # Horizontal scrollbar
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        hsb.grid(row=1, column=0, sticky="ew")

        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Configure columns (heading text, width, alignment, sorting command)
        for col in columns:
            anchor = tk.W # Default left-align
            width = 90
            # Adjust width/alignment for specific columns
            if col in ('Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Qty', 'Price', 'Total Val', 'Quantity', 'Tick'):
                anchor = tk.E; width=70
            if col == 'Reason': width = 250
            if col == 'Good': width = 80
            if col == 'From' or col == 'To': width = 100

            # Add sorting capability to each column header
            tree.heading(col, text=col, command=lambda c=col: self._sort_treeview_column(tree, c, False))
            tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        return tree

    def _sort_treeview_column(self, tv, col, reverse):
        """Sorts a Treeview column when its header is clicked."""
        try:
            # Get data from the column, converting to float if possible for numeric sort
            l = []
            for k in tv.get_children(''):
                val = tv.set(k, col)
                try:
                    l.append((float(val), k))
                except ValueError:
                    l.append((val.lower(), k)) # Fallback to case-insensitive string sort

            # Perform the sort
            l.sort(key=lambda t: t[0], reverse=reverse)

            # Reorder items in the treeview
            for index, (val, k) in enumerate(l):
                tv.move(k, '', index)

            # Update the heading command to toggle sort direction
            tv.heading(col, command=lambda c=col: self._sort_treeview_column(tv, c, not reverse))
        except Exception as e:
            # Catch potential errors during sorting
            print(f"Error sorting treeview column {col}: {e}")

    def _safe_format_float(self, value, format_spec=".1f", default_val='?'):
        """Safely formats a value as a float, returning default if not possible."""
        # Deprecated - Using direct f-string formatting now, but kept for reference
        if isinstance(value, (int, float)):
            try:
                return f"{value:{format_spec}}"
            except (ValueError, TypeError):
                return str(value) # Fallback if formatting fails
        else:
            try:
                # Attempt conversion for string representations of numbers
                return f"{float(value):{format_spec}}"
            except (ValueError, TypeError):
                 return default_val # Return default if not convertible

    def _update_trade_analysis_window(self):
        """Updates the data displayed in the trade analysis window."""
        # Check if window exists and is valid
        if not self.analysis_window or not self.analysis_window.winfo_exists(): return
        # Update window title with current tick
        self.analysis_window.title(f"Trade & Migration Analysis (Tick {self.world.tick})")

        # --- Update Executed Trades Tab ---
        if self.analysis_tree_executed:
            self.analysis_tree_executed.delete(*self.analysis_tree_executed.get_children()) # Clear old data
            # Sort by profit? Already sorted by world logic, but could re-sort here if needed
            for trade in self.world.executed_trade_details_this_tick:
                values = (
                    trade['seller_name'], trade['buyer_name'], trade['good_name'],
                    f"{trade['quantity']:.1f}", f"{trade['seller_price']:.2f}",
                    f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}",
                    f"{trade['quantity'] * trade['seller_price']:.1f}" # Total value
                )
                try: self.analysis_tree_executed.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting executed trade: {e}")

        # --- Update Failed Trades Tab ---
        if self.analysis_tree_failed:
            self.analysis_tree_failed.delete(*self.analysis_tree_failed.get_children()) # Clear old data
            # Sort failed trades by potential profit (descending) for better analysis
            sorted_failed = sorted(self.world.failed_trades_this_tick, key=lambda x: x.get('profit_per_unit', 0), reverse=True)
            for trade in sorted_failed:
                 # Use direct f-string formatting with error handling (though less likely needed now)
                 qty_avail_str = f"{trade.get('qty_avail', '?'):.1f}" if isinstance(trade.get('qty_avail'), (int,float)) else '?'
                 pot_qty_str = f"{trade.get('potential_qty', '?'):.1f}" if isinstance(trade.get('potential_qty'), (int,float)) else '?'
                 values = (
                    trade['seller_name'], trade['buyer_name'], trade['good_name'],
                    f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}",
                    f"{trade['profit_per_unit']:.2f}",
                    qty_avail_str, pot_qty_str,
                    trade.get('fail_reason', 'Unknown') # Display failure reason
                 )
                 try: self.analysis_tree_failed.insert("", tk.END, values=values)
                 except Exception as e: print(f"Error inserting failed trade: {e}")

        # --- Update Potential Trades Tab ---
        if self.analysis_tree_potential:
            self.analysis_tree_potential.delete(*self.analysis_tree_potential.get_children()) # Clear old data
            # Filter for trades marked as preliminarily viable by find_trade_opportunities
            viable_potential = [t for t in self.world.potential_trades_this_tick if t.get('is_viable_prelim', False)]
            # Sort by profit (descending)
            sorted_potential = sorted(viable_potential, key=lambda x: x['profit_per_unit'], reverse=True)
            for trade in sorted_potential:
                values = (
                    trade['seller_name'], trade['buyer_name'], trade['good_name'],
                    f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}",
                    f"{trade['profit_per_unit']:.2f}", f"{trade['qty_avail']:.1f}",
                    f"{trade['potential_qty']:.1f}"
                )
                try: self.analysis_tree_potential.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting potential trade: {e}")

        # --- Update Migration Tab ---
        if self.analysis_tree_migration:
            self.analysis_tree_migration.delete(*self.analysis_tree_migration.get_children()) # Clear old data
            # Iterate through the migration details recorded in the World object
            total_migrants = 0
            for migration in self.world.migration_details_this_tick:
                values = (
                    migration['tick'],
                    migration['from_name'],
                    migration['to_name'],
                    migration['quantity']
                )
                total_migrants += migration['quantity']
                try: self.analysis_tree_migration.insert("", tk.END, values=values)
                except Exception as e: print(f"Error inserting migration event: {e}")

            # Optional: Add summary info (e.g., total migrants)
            # Could add a label above or below the treeview in the mig_frame
            # print(f"DEBUG: Total migrants this tick: {total_migrants}") # Example debug print

    def _on_analysis_window_close(self):
        """Callback function when the analysis window is closed."""
        if self.analysis_window:
            self.analysis_window.destroy()
            # Clear references to the window and its treeviews
            self.analysis_window = None
            self.analysis_tree_potential = None
            self.analysis_tree_failed = None
            self.analysis_tree_executed = None
            self.analysis_tree_migration = None # <<< Clear migration tree reference

    # --- Main Update Loop ---
    def update_simulation(self):
        """Performs one tick of the simulation and updates the UI."""
        # Stop loop if simulation is paused
        if not self.simulation_running:
            # Still check periodically if paused, in case user resumes
            self.root.after(100, self.update_simulation)
            return
        # Stop loop if the main window has been closed
        if not self.root.winfo_exists():
            print("Root window closed, stopping simulation loop.")
            return

        try:
            # --- 1. Run Simulation Step ---
            start_tick_time = time.time()
            self.world.simulation_step() # Execute one tick of game logic

            # --- 2. Update Tick Label ---
            self.tick_label_var.set(f"Tick: {self.world.tick}")

            # --- 3. Update Dynamic Settlement State Table ---
            # Get current list of settlements (might have changed due to abandonment)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            # Update settlement coordinates dictionary (includes z now)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}

            # Get IDs currently in the treeview vs IDs in the simulation
            current_tree_items = set(self.dynamic_tree.get_children())
            settlement_ids_in_world = set(s.id for s in self.settlements)

            # Update or insert rows for current settlements
            for settlement in self.settlements:
                # Format data for the row
                storage_load = settlement.get_current_storage_load()
                storage_cap = settlement.storage_capacity
                storage_str = f"{storage_load:.1f}/{storage_cap:.0f}"
                labor_str = f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}"
                values = [settlement.name, labor_str, f"{settlement.wealth:.0f}", storage_str]
                for good in self.sorted_goods:
                    price = settlement.local_prices.get(good.id)
                    stored = settlement.get_total_stored(good.id)
                    values.append(f"{price:.2f}" if price is not None else "N/A")
                    values.append(f"{stored:.1f}" if stored > 1e-6 else "0.0")

                # Update existing item or insert new one
                if settlement.id in current_tree_items:
                    try: self.dynamic_tree.item(settlement.id, values=values)
                    except tk.TclError: pass # Ignore if item somehow deleted between check and update
                else:
                    try: self.dynamic_tree.insert("", tk.END, iid=settlement.id, values=values)
                    except tk.TclError: pass # Ignore if item somehow added between check and update

            # Remove rows for settlements that no longer exist (abandoned)
            ids_to_remove_from_tree = current_tree_items - settlement_ids_in_world
            for item_id in ids_to_remove_from_tree:
                try: self.dynamic_tree.delete(item_id)
                except tk.TclError: pass # Ignore if already deleted

            # --- 4. Update Trade Log ---
            self.trade_log_text.config(state=tk.NORMAL) # Enable editing
            self.trade_log_text.delete('1.0', tk.END)   # Clear old log
            log_content = "\n".join(self.world.recent_trades_log) if self.world.recent_trades_log else "- No trades yet -"
            self.trade_log_text.insert(tk.END, log_content) # Insert new log content
            self.trade_log_text.config(state=tk.DISABLED) # Disable editing
            self.trade_log_text.yview_moveto(1.0) # Scroll to the bottom

            # --- 5. Update Visualization & Analysis Window ---
            last_trade_details = None # Track last trade for map info display
            if hasattr(self, 'map_canvas') and self.map_canvas.winfo_exists():
                # Update settlement visuals (size, color, text) on the map
                self._update_settlement_visuals()
                # Draw effects for trades that happened this tick
                trades_this_tick = list(self.world.executed_trade_details_this_tick)
                if trades_this_tick:
                    for trade_info in trades_this_tick:
                        self._draw_trade_route(trade_info)
                        last_trade_details = trade_info # Store the last one for display
                else:
                    # Clear last trade info if no trades occurred
                    self.last_trade_info_var.set("No trades this tick.")
                    self.last_trade_reason_var.set("")

            # Update the info labels below the map if there was a trade
            if last_trade_details:
                info_text = (f"Trade: {last_trade_details['quantity']:.1f} {last_trade_details['good_name']} "
                             f"from {last_trade_details['seller_name']} to {last_trade_details['buyer_name']}")
                reason_text = (f"Reason: Seller Price={last_trade_details['seller_price']:.2f}, "
                               f"Buyer Price={last_trade_details['buyer_price']:.2f} "
                               f"(Profit/Unit={last_trade_details['profit_per_unit']:.2f})")
                self.last_trade_info_var.set(info_text)
                self.last_trade_reason_var.set(reason_text)

            # Update the data in the analysis window (if it's open)
            self._update_trade_analysis_window()

            # --- 6. Schedule Next Update ---
            tick_duration = time.time() - start_tick_time
            delay = max(10, TICK_DELAY_MS - int(tick_duration * 1000)) # Calculate delay, ensuring minimum 10ms
            # print(f"  Tick {self.world.tick} duration: {tick_duration:.4f}s, Next update in: {delay}ms")
            if self.simulation_running:
                self.root.after(delay, self.update_simulation)

        except Exception as e:
            # Catch any errors during the simulation step or UI update
            print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---")
            traceback.print_exc()
            # Attempt to gracefully quit the application on error
            if self.root.winfo_exists():
                self.root.quit()

# --- Main Execution ---
if __name__ == "__main__":
    # Standard Tkinter setup
    root = tk.Tk()
    try:
        # Create and run the UI application
        app = SimulationUI(root)
        root.mainloop() # Start the Tkinter event loop
    except Exception as e:
        # Catch fatal errors during UI initialization
        print(f"\n--- FATAL ERROR INITIALIZING UI ---")
        traceback.print_exc()
    finally:
        # Message indicating application closure
        print("UI Closed / Application Finished.")

