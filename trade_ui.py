import tkinter as tk
from tkinter import ttk
import time
import textwrap # For formatting recipes
import traceback # Import traceback for better error printing

# --- Import ttk theme library ---
try:
    import sv_ttk
    SV_TTK_AVAILABLE = True
except ImportError:
    print("WARN: 'sv_ttk' library not found. UI will use default theme.")
    print("      Install using: pip install sv_ttk")
    SV_TTK_AVAILABLE = False

# --- Import Simulation Logic & Setup ---
try:
    from trade_logic import World, Good, Settlement, ItemInstance # Import necessary classes
except ImportError:
    print("ERROR: Make sure 'trade_logic.py' exists in the same directory.")
    exit()
try:
    from world_setup import setup_world
except ImportError:
    print("ERROR: Make sure 'world_setup.py' exists in the same directory.")
    exit()

# --- UI Constants ---
TICK_DELAY_MS = 500
WINDOW_TITLE = "Emergent Trade Simulation"
DARK_BG = "#2e2e2e"
DARK_FG = "#cccccc"
DARK_INSERT_BG = "#555555"

# --- Main Simulation UI Class ---
class SimulationUI:
    """Main class for the Tkinter UI (Single Window)."""

    def __init__(self, root):
        """Initialize the UI and the simulation world."""
        self.root = root
        self.root.title(WINDOW_TITLE)
        # Make window fullscreen (zoomed state)
        try:
            # Cross-platform way to maximize
            self.root.state('zoomed')
        except tk.TclError:
            # Fallback for some systems if 'zoomed' is not available
            print("WARN: Could not zoom window, attempting maximize.")
            try:
                 # May not work on all OS/window managers
                 w, h = root.winfo_screenwidth(), root.winfo_screenheight()
                 root.geometry(f"{w}x{h}+0+0")
            except Exception as e:
                 print(f"WARN: Could not maximize window: {e}")


        # --- Set the theme ---
        self._apply_theme()

        # --- Initialize World ---
        print("Setting up world (using world_setup.py)...")
        try:
            self.world = setup_world()
            self.sorted_goods = sorted(self.world.goods.values(), key=lambda g: g.id)
            self.settlements = sorted(self.world.get_all_settlements(), key=lambda s: s.id)
            print("World setup complete.")
        except Exception as e:
            print(f"\n--- ERROR DURING WORLD SETUP ---"); print(e); traceback.print_exc(); print("-" * 30)
            self.root.quit(); return

        # --- Main Layout Frames ---
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # Configure root grid to expand
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Configure main_frame grid for two panes (static left, dynamic right)
        self.main_frame.columnconfigure(0, weight=1) # Static pane weight (adjust ratio as needed)
        self.main_frame.columnconfigure(1, weight=3) # Dynamic pane weight
        self.main_frame.rowconfigure(1, weight=1) # Allow row containing panes to expand vertically

        # --- Top Info Bar (Tick) ---
        self.tick_label_var = tk.StringVar(value="Tick: 0")
        self.tick_label = ttk.Label(self.main_frame, textvariable=self.tick_label_var, font=("Arial", 14, "bold"))
        # Span across both columns
        self.tick_label.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))

        # --- Setup Panes ---
        self._setup_static_pane()
        self._setup_dynamic_pane()

        # --- Start Simulation Loop ---
        print("Starting simulation loop...")
        try:
             self.update_simulation()
        except Exception as e:
            print(f"\n--- ERROR ON FIRST SIMULATION UPDATE ---"); print(e); traceback.print_exc(); print("-" * 30)
            self.root.quit()

    def _apply_theme(self):
        """Applies the dark theme."""
        if SV_TTK_AVAILABLE:
            print("Applying sv_ttk dark theme...")
            sv_ttk.set_theme("dark")
        else: # Fallback theme setup
            print("Applying basic fallback dark theme...")
            style = ttk.Style()
            try:
                theme = 'clam' if 'clam' in style.theme_names() else 'alt'
                style.theme_use(theme); print(f"Using fallback theme: {theme}")
            except Exception as e: print(f"WARN: Could not set fallback ttk theme: {e}")
            self.root.config(bg=DARK_BG)
            style.configure('.', background=DARK_BG, foreground=DARK_FG)
            style.configure('TFrame', background=DARK_BG); style.configure('TLabel', background=DARK_BG, foreground=DARK_FG)
            style.configure('TLabelFrame', background=DARK_BG, foreground=DARK_FG); style.configure('TLabelFrame.Label', background=DARK_BG, foreground=DARK_FG)
            style.configure('Treeview', background="#3f3f3f", foreground=DARK_FG, fieldbackground="#3f3f3f")
            style.configure('Treeview.Heading', background="#4a4a4a", foreground=DARK_FG); style.map('Treeview', background=[('selected', '#5a5a5a')], foreground=[('selected', 'white')])
            style.configure('TScrollbar', background=DARK_BG, troughcolor="#4a4a4a")

    def _setup_static_pane(self):
        """Sets up the widgets for the left (static info) pane."""
        static_pane = ttk.Frame(self.main_frame, padding="5")
        static_pane.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        static_pane.rowconfigure(1, weight=1) # Allow settlements tree to expand
        static_pane.rowconfigure(3, weight=1) # Allow goods tree to expand
        static_pane.rowconfigure(5, weight=2) # Allow recipe text to expand
        static_pane.columnconfigure(0, weight=1)

        # --- Settlements Info ---
        ttk.Label(static_pane, text="Settlements", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self._create_settlements_treeview(static_pane)
        self.settlements_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        settlements_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.settlements_tree.yview)
        self.settlements_tree.configure(yscrollcommand=settlements_scrollbar.set)
        settlements_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))

        # --- Goods Info ---
        ttk.Label(static_pane, text="Goods", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self._create_goods_treeview(static_pane)
        self.goods_tree.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        goods_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.goods_tree.yview)
        self.goods_tree.configure(yscrollcommand=goods_scrollbar.set)
        goods_scrollbar.grid(row=3, column=1, sticky=(tk.N, tk.S))

        # Bind selection event to goods treeview
        self.goods_tree.bind("<<TreeviewSelect>>", self._on_good_select)

        # --- Recipe Info ---
        ttk.Label(static_pane, text="Recipe Details", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
        self.recipe_text = tk.Text(
            static_pane, wrap=tk.WORD, state=tk.DISABLED, height=10,
            bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_FG,
            borderwidth=1, relief=tk.SUNKEN)
        recipe_scrollbar = ttk.Scrollbar(static_pane, orient=tk.VERTICAL, command=self.recipe_text.yview)
        self.recipe_text.config(yscrollcommand=recipe_scrollbar.set)
        self.recipe_text.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        recipe_scrollbar.grid(row=5, column=1, sticky=(tk.N, tk.S))
        # Initial message
        self._update_recipe_display("(Select a good above to see its recipe)")


    def _create_settlements_treeview(self, parent):
        """Creates the Treeview for static settlement data."""
        columns = ["id", "name", "terrain", "pop"]
        column_names = ["ID", "Name", "Terrain", "Population"]
        self.settlements_tree = ttk.Treeview(parent, columns=columns, show="headings", height=8)
        for col, name in zip(columns, column_names):
            self.settlements_tree.heading(col, text=name)
            width = 100; anchor = tk.W
            if col == "id": width = 30
            elif col == "pop": width = 60; anchor = tk.E
            self.settlements_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        # Populate
        for settlement in self.settlements:
            values = [settlement.id, settlement.name, settlement.terrain_type, settlement.population]
            self.settlements_tree.insert("", tk.END, values=values)

    def _create_goods_treeview(self, parent):
        """Creates the Treeview for static goods data."""
        columns = ["id", "name", "base_value", "producible"]
        column_names = ["ID", "Name", "Base Value", "Producible?"]
        self.goods_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
        for col, name in zip(columns, column_names):
            self.goods_tree.heading(col, text=name)
            width = 80; anchor = tk.W
            if col == "base_value": anchor = tk.E
            self.goods_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
        # Populate
        for good in self.sorted_goods:
            values = [good.id, good.name, f"{good.base_value:.1f}", "Yes" if good.is_producible else "No"]
            # Use good.id as the item identifier (iid) for easy lookup later
            self.goods_tree.insert("", tk.END, iid=good.id, values=values)

    def _on_good_select(self, event):
        """Callback when a good is selected in the goods Treeview."""
        selected_items = self.goods_tree.selection()
        if not selected_items:
            self._update_recipe_display("(Select a good above to see its recipe)")
            return

        selected_iid = selected_items[0] # Get the first selected item's iid (which is the good.id)
        selected_good = self.world.goods.get(selected_iid)

        if selected_good and selected_good.recipe:
            recipe = selected_good.recipe
            recipe_str = f"** {selected_good.name} ({selected_good.id}) **\n"
            inputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['inputs'].items()]) if recipe['inputs'] else "None"
            recipe_str += f"  Inputs: {inputs_str}\n"
            outputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['outputs'].items()])
            recipe_str += f"  Outputs: {outputs_str}\n"
            recipe_str += f"  Labor Cost: {recipe['labor']:.1f}\n"
            if recipe['wealth_cost'] > 0: recipe_str += f"  Wealth Cost: {recipe['wealth_cost']:.1f}\n"
            if recipe['required_terrain']: terrain_str = ", ".join(recipe['required_terrain']); recipe_str += f"  Requires Terrain: {terrain_str}\n"
            self._update_recipe_display(recipe_str)
        elif selected_good:
             self._update_recipe_display(f"** {selected_good.name} ({selected_good.id}) **\n\n(Not producible or no recipe defined)")
        else:
             self._update_recipe_display("(Error: Could not find selected good)")

    def _update_recipe_display(self, text_content):
        """Clears and updates the recipe Text widget."""
        self.recipe_text.config(state=tk.NORMAL)
        self.recipe_text.delete('1.0', tk.END)
        self.recipe_text.insert(tk.END, text_content)
        self.recipe_text.config(state=tk.DISABLED)


    def _setup_dynamic_pane(self):
        """Sets up the widgets for the right (dynamic info) pane."""
        dynamic_pane = ttk.Frame(self.main_frame, padding="5")
        dynamic_pane.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        dynamic_pane.rowconfigure(1, weight=3) # Give more weight to dynamic table
        dynamic_pane.rowconfigure(3, weight=1) # Weight for trade log
        dynamic_pane.columnconfigure(0, weight=1)

        # --- Dynamic State Table ---
        ttk.Label(dynamic_pane, text="Settlement State", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        self._create_dynamic_treeview(dynamic_pane)
        self.dynamic_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dynamic_scrollbar_y = ttk.Scrollbar(dynamic_pane, orient=tk.VERTICAL, command=self.dynamic_tree.yview)
        dynamic_scrollbar_x = ttk.Scrollbar(dynamic_pane, orient=tk.HORIZONTAL, command=self.dynamic_tree.xview)
        self.dynamic_tree.configure(yscrollcommand=dynamic_scrollbar_y.set, xscrollcommand=dynamic_scrollbar_x.set)
        dynamic_scrollbar_y.grid(row=1, column=1, sticky=(tk.N, tk.S))
        dynamic_scrollbar_x.grid(row=2, column=0, sticky=(tk.W, tk.E))

        # --- Trade Log ---
        ttk.Label(dynamic_pane, text="Recent Trades", font=("Arial", 12, "bold")).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        self.trade_log_text = tk.Text(
            dynamic_pane, height=8, width=80, wrap=tk.WORD, state=tk.DISABLED,
            bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_FG,
            borderwidth=1, relief=tk.SUNKEN )
        trade_log_scrollbar = ttk.Scrollbar(dynamic_pane, orient=tk.VERTICAL, command=self.trade_log_text.yview)
        self.trade_log_text.config(yscrollcommand=trade_log_scrollbar.set)
        self.trade_log_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        trade_log_scrollbar.grid(row=4, column=1, sticky=(tk.N, tk.S))


    def _create_dynamic_treeview(self, parent):
        """Creates the Treeview widget for displaying dynamic settlement data."""
        # Define columns (ID is implicit iid)
        columns = ["name", "labor", "wealth", "storage"]
        column_names = ["Settlement", "Labor", "Wealth", "Storage"]
        for good in self.sorted_goods:
            columns.append(f"{good.id}_price"); column_names.append(f"{good.name} Price")
            columns.append(f"{good.id}_stored"); column_names.append(f"{good.name} Stored")

        self.dynamic_tree = ttk.Treeview(parent, columns=columns, show="headings") # Height determined by grid weight

        for col, name in zip(columns, column_names):
            self.dynamic_tree.heading(col, text=name)
            width = 80
            if col == "name": width = 100; anchor = tk.W
            elif col in ["wealth", "labor", "storage"]: width = 90; anchor = tk.E
            elif "_price" in col: width = 70; anchor = tk.E
            elif "_stored" in col: width = 70; anchor = tk.E
            else: anchor = tk.W # Default
            self.dynamic_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)


    def update_simulation(self):
        """Runs one simulation step and updates the main UI."""
        try:
            # 1. Run simulation step
            self.world.simulation_step()

            # 2. Update Tick Label
            self.tick_label_var.set(f"Tick: {self.world.tick}")

            # 3. Update Dynamic Treeview Table
            # Use settlement ID as the item identifier (iid)
            for settlement in self.settlements: # Use the stored sorted list
                storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
                storage_str = f"{storage_load:.1f}/{storage_cap:.0f}"
                labor_str = f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}" # Labor shown *after* production step

                values = [
                    settlement.name, labor_str, f"{settlement.wealth:.0f}", storage_str,
                ]
                for good in self.sorted_goods:
                    price = settlement.local_prices.get(good.id)
                    stored = settlement.get_total_stored(good.id)
                    values.append(f"{price:.2f}" if price is not None else "N/A")
                    values.append(f"{stored:.1f}" if stored > 1e-6 else "0.0")

                # Check if item exists before updating or inserting
                if self.dynamic_tree.exists(settlement.id):
                    try:
                        self.dynamic_tree.item(settlement.id, values=values)
                    except tk.TclError as e:
                        print(f"WARN: TclError updating item {settlement.id}: {e}.")
                else:
                    try:
                        self.dynamic_tree.insert("", tk.END, iid=settlement.id, values=values)
                    except tk.TclError as e:
                         print(f"WARN: TclError inserting item {settlement.id}: {e}.")


            # 4. Update Trade Log
            self.trade_log_text.config(state=tk.NORMAL)
            self.trade_log_text.delete('1.0', tk.END)
            log_content = "\n".join(self.world.recent_trades) if self.world.recent_trades else "- No trades yet -"
            self.trade_log_text.insert(tk.END, log_content)
            self.trade_log_text.config(state=tk.DISABLED)
            self.trade_log_text.yview_moveto(1.0) # Scroll to end

            # 5. Schedule the next update
            if self.root.winfo_exists():
                self.root.after(TICK_DELAY_MS, self.update_simulation)
            else:
                print("Root window closed, stopping simulation loop.")

        except Exception as e:
            print(f"\n--- ERROR DURING SIMULATION/UPDATE (Tick {self.world.tick}) ---"); print(e); traceback.print_exc(); print("-" * 30)
            if self.root.winfo_exists(): self.root.quit()


# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = SimulationUI(root)
        # No need to set minsize if using 'zoomed' state
        root.mainloop()
    except Exception as e:
         print(f"\n--- FATAL ERROR INITIALIZING UI ---"); print(e); traceback.print_exc(); print("-" * 30)
    finally:
        print("UI Closed / Application Finished.")

