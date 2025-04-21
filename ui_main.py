import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import time
import traceback
import sys
import json

# --- Import Simulation Logic & Setup ---
try:
    from trade_logic import World
    from world_setup import setup_world
except ImportError:
    print("ERROR: Make sure 'trade_logic.py' and 'world_setup.py' exist and are runnable.")
    sys.exit(1)

# --- Import UI Modules ---
try:
    import ui_static_pane
    import ui_dynamic_pane
    import ui_map_pane
    import ui_analysis_window
    # import ui_components # Commented out as it doesn't exist yet
except ImportError as e:
    print(f"ERROR: Failed to import UI module: {e}")
    print("Ensure ui_static_pane.py, ui_dynamic_pane.py, ui_map_pane.py, ui_analysis_window.py exist.")
    sys.exit(1)

# --- Import Theme ---
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    print("WARN: 'sv_ttk' library not found. UI will use default theme.")
    SV_TTK_AVAILABLE = False

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

# --- Theme colors ---
DARK_BG = "#2e2e2e"; DARK_FG = "#cccccc"; DARK_INSERT_BG = "#555555"
CANVAS_BG = "#1e1e1e"; SETTLEMENT_COLOR = "#4a90e2"; WEALTH_TEXT_COLOR = "#ffffff"
TRADE_ROUTE_COLOR = "#f5a623"; TRADE_ROUTE_FLASH_COLOR = "#ffffff"; TRADE_MARKER_COLOR = "#50e3c2"


# --- Main Simulation UI Class ---
class SimulationUI:
    """
    Manages the main Tkinter window, simulation state, and coordinates updates
    across different UI panes/modules.
    """

    def __init__(self, root):
        """Initializes the UI, sets up the world, and creates widgets by calling module setup functions."""
        self.root = root
        self.root.title(ui_params['window_title'])
        try: self.root.state('zoomed')
        except tk.TclError: print("WARN: Could not zoom window.")

        # --- Store Constants and Theme Info on Instance ---
        self.TICK_DELAY_MS = ui_params['tick_delay_ms']
        self.TRADE_EFFECT_DURATION_MS = ui_params['trade_effect_duration_ms']
        self.SETTLEMENT_BASE_RADIUS = ui_params['settlement_base_radius']
        self.SETTLEMENT_WEALTH_SCALE_PARAM = ui_params.get('settlement_wealth_sqrt_scale', 0.5)
        self.SETTLEMENT_MAX_RADIUS_INCREASE = ui_params['settlement_max_radius_increase']
        self.TRADE_MARKER_RADIUS = ui_params['trade_marker_radius']
        self.CITY_COLOR = ui_params.get('city_color', "#e27a7a")
        self.CITY_POP_THRESHOLD = sim_params_for_ui['city_population_threshold']
        self.DARK_BG = DARK_BG; self.DARK_FG = DARK_FG; self.DARK_INSERT_BG = DARK_INSERT_BG
        self.CANVAS_BG = CANVAS_BG; self.SETTLEMENT_COLOR = SETTLEMENT_COLOR; self.WEALTH_TEXT_COLOR = WEALTH_TEXT_COLOR
        self.TRADE_ROUTE_COLOR = TRADE_ROUTE_COLOR; self.TRADE_ROUTE_FLASH_COLOR = TRADE_ROUTE_FLASH_COLOR; self.TRADE_MARKER_COLOR = TRADE_MARKER_COLOR
        self.SV_TTK_AVAILABLE = SV_TTK_AVAILABLE

        self._apply_theme()
        # <<< Initialize simulation as PAUSED >>>
        self.simulation_running = False

        # --- Simulation State ---
        print("Setting up world...")
        try:
            self.world = setup_world(config_file="config.json", recipe_file="recipes.json")
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            print("World setup complete.")
        except Exception as e:
            print(f"\n--- ERROR DURING WORLD SETUP ---"); print(e); traceback.print_exc(); self.root.quit(); return

        # --- UI Widget References ---
        self.settlements_tree = None; self.goods_tree = None; self.recipe_text = None; self.global_totals_tree = None
        self.scrollable_canvas = None; self.scrollable_frame = None; self.canvas_frame_id = None
        self.settlement_widgets = {}
        self.map_canvas = None; self.settlement_canvas_items = {}
        self.settlement_font = tkFont.Font(family="Arial", size=9)
        self.wealth_font = tkFont.Font(family="Arial", size=10, weight="bold")
        self.analysis_window = None; self.analysis_tree_potential = None; self.analysis_tree_failed = None
        self.analysis_tree_executed = None; self.analysis_tree_migration = None

        # --- Tkinter Variables ---
        self.last_trade_info_var = tk.StringVar(value="No trades yet this tick.")
        self.last_trade_reason_var = tk.StringVar(value="")
        self.tick_label_var = tk.StringVar(value="Tick: 0")

        # --- Create Main UI Layout ---
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1, minsize=300)
        self.main_frame.columnconfigure(1, weight=4, minsize=600)
        self.main_frame.rowconfigure(1, weight=1)

        # --- Control Bar ---
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.tick_label = ttk.Label(control_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        self.tick_label.pack(side=tk.LEFT, padx=(0, 20))
        # <<< Set initial button states for PAUSED >>>
        self.start_button = ttk.Button(control_frame, text="Start", command=self._start_sim, state=tk.NORMAL)
        self.start_button.pack(side=tk.LEFT, padx=5)
        self.pause_button = ttk.Button(control_frame, text="Pause", command=self._pause_sim, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        analysis_button = ttk.Button(control_frame, text="Trade Analysis", command=lambda: ui_analysis_window.open_analysis_window(self))
        analysis_button.pack(side=tk.LEFT, padx=5)

        # --- Setup Content Panes via Modules ---
        self.static_pane_frame = ttk.Frame(self.main_frame, padding="5")
        self.static_pane_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        ui_static_pane.setup_static_pane(self.static_pane_frame, self)

        self._setup_notebook() # Setup notebook locally

        print("Starting simulation loop (initially paused)...")
        try:
             ui_map_pane.create_settlement_canvas_items(self) # Initial map draw
             ui_dynamic_pane.update_dynamic_pane(self) # Initial dynamic pane population
             ui_static_pane.update_global_totals_display(self) # Initial global totals
             # Schedule the loop - it will check self.simulation_running
             self.root.after(self.TICK_DELAY_MS, self.update_simulation)
        except Exception as e:
             print(f"\n--- ERROR ON FIRST SIMULATION START ---"); print(e); traceback.print_exc(); self.root.quit()

    # --- Simulation Control Methods ---
    def _pause_sim(self):
        """Pauses the simulation update loop."""
        # This button should only be clickable if running=True
        if self.simulation_running:
            self.simulation_running = False
            self.pause_button.config(state=tk.DISABLED)
            self.start_button.config(state=tk.NORMAL)
            print("--- Simulation Paused ---")
    def _start_sim(self):
        """Starts or resumes the simulation update loop."""
        # This button should only be clickable if running=False
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
        if self.SV_TTK_AVAILABLE:
            sv_ttk.set_theme("dark"); self.root.configure(bg=self.DARK_BG)
        else:
             print("Applying basic fallback dark theme..."); style = ttk.Style()
             theme_to_use = 'clam' if 'clam' in style.theme_names() else 'alt'
             try: style.theme_use(theme_to_use)
             except tk.TclError: print(f"WARN: Could not use theme '{theme_to_use}'. Using default.")
             self.root.config(bg=self.DARK_BG); style.configure('.', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('TFrame', background=self.DARK_BG); style.configure('TLabel', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('TLabelFrame', background=self.DARK_BG, foreground=self.DARK_FG); style.configure('TLabelFrame.Label', background=self.DARK_BG, foreground=self.DARK_FG)
             style.configure('Treeview', background="#3f3f3f", foreground=self.DARK_FG, fieldbackground="#3f3f3f")
             style.configure('Treeview.Heading', background="#4a4a4a", foreground=self.DARK_FG); style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
             style.configure('TScrollbar', background=self.DARK_BG, troughcolor="#4a4a4a"); style.configure("TNotebook", background=self.DARK_BG, borderwidth=0)
             style.configure("TNotebook.Tab", background="#4a4a4a", foreground=self.DARK_FG, padding=[5, 2], borderwidth=0); style.map("TNotebook.Tab", background=[("selected", self.SETTLEMENT_COLOR)], foreground=[("selected", "white")])

    # --- UI Setup: Notebook ---
    def _setup_notebook(self):
        """Sets up the right pane notebook with tabs."""
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=1, column=1, sticky="nsew", padx=(5,0))
        # Settlement Details Tab
        self.dynamic_pane_frame = ttk.Frame(self.notebook, padding="5")
        self.dynamic_pane_frame.grid(row=0, column=0, sticky="nsew")
        self.dynamic_pane_frame.rowconfigure(0, weight=1); self.dynamic_pane_frame.columnconfigure(0, weight=1)
        ui_dynamic_pane.setup_dynamic_pane(self.dynamic_pane_frame, self)
        # Map Tab
        self.viz_pane_frame = ttk.Frame(self.notebook, padding="5")
        self.viz_pane_frame.grid(row=0, column=0, sticky="nsew")
        self.viz_pane_frame.rowconfigure(1, weight=1); self.viz_pane_frame.columnconfigure(0, weight=1)
        ui_map_pane.setup_map_pane(self.viz_pane_frame, self)
        self.notebook.add(self.dynamic_pane_frame, text='Settlement Details')
        self.notebook.add(self.viz_pane_frame, text='Map')

    # --- Main Update Loop ---
    def update_simulation(self):
        """Performs one tick of the simulation and calls UI update functions from modules."""
        # --- Check if running ---
        if not self.simulation_running:
            # If paused, just reschedule the check without running sim/updates
            self.root.after(100, self.update_simulation)
            return
        # --- Check if window closed ---
        if not self.root.winfo_exists():
            print("Root window closed, stopping simulation loop.")
            return

        # --- Run simulation and update UI ---
        try:
            start_tick_time = time.time()
            self.world.simulation_step() # 1. Run Sim Step
            self.tick_label_var.set(f"Tick: {self.world.tick}") # 2. Update Tick Label
            # 3. Update Core Data Lists
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            self.settlement_coords = {s.id: (s.x, s.y, s.z) for s in self.settlements}
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            # 4. Update UI Panes via Module Functions
            ui_static_pane.update_static_pane(self)
            ui_dynamic_pane.update_dynamic_pane(self)
            ui_map_pane.update_map_pane(self)
            ui_analysis_window.update_analysis_window(self) # This now checks internally if window exists
            # 5. Schedule Next Update
            tick_duration = time.time() - start_tick_time
            delay = max(10, self.TICK_DELAY_MS - int(tick_duration * 1000))
            # Check simulation_running again before scheduling next call
            if self.simulation_running:
                self.root.after(delay, self.update_simulation)
        except Exception as e:
            print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---"); traceback.print_exc()
            if self.root.winfo_exists(): self.root.quit()

# --- Main Execution Block ---
if __name__ == "__main__":
    """Entry point for the application."""
    root = tk.Tk()
    try: app = SimulationUI(root); root.mainloop()
    except Exception as e: print(f"\n--- FATAL ERROR INITIALIZING UI ---"); traceback.print_exc()
    finally: print("UI Closed / Application Finished.")
