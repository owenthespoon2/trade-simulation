import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
from trade_logic import Good # Import Good

def setup_static_pane(parent_frame, app):
    """
    Sets up the widgets within the static (left) pane of the main window.

    Args:
        parent_frame (ttk.Frame): The parent frame for this pane.
        app (SimulationUI): The main application instance, used to access data
                            and store widget references.
    """
    # Configure row weights for vertical expansion
    parent_frame.rowconfigure(1, weight=1) # Settlements treeview
    parent_frame.rowconfigure(3, weight=1) # Goods treeview
    parent_frame.rowconfigure(5, weight=1) # Recipe text area
    parent_frame.rowconfigure(7, weight=1) # Global Totals treeview
    parent_frame.rowconfigure(9, weight=1) # Global Average Prices treeview
    parent_frame.rowconfigure(11, weight=1) # NEW: Global Trade Volume treeview
    parent_frame.columnconfigure(0, weight=1) # Allow content to expand horizontally

    DARK_BG = app.root.cget('bg')
    DARK_FG = "#cccccc"
    DARK_INSERT_BG = "#555555"

    # --- Settlements List ---
    ttk.Label(parent_frame, text="Settlements", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
    columns = ["id", "name", "terrain", "pop"]; column_names = ["ID", "Name", "Terrain", "Pop"]
    app.settlements_tree = ttk.Treeview(parent_frame, columns=columns, show="headings", height=5)
    for col, name in zip(columns, column_names):
        app.settlements_tree.heading(col, text=name); width = 100; anchor = tk.W
        if col == "id": width = 30
        elif col == "pop": width = 60; anchor = tk.E
        app.settlements_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    _create_settlements_treeview(app)
    app.settlements_tree.grid(row=1, column=0, sticky="ewns")
    settlements_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.settlements_tree.yview)
    app.settlements_tree.configure(yscrollcommand=settlements_scrollbar.set); settlements_scrollbar.grid(row=1, column=1, sticky="ns")

    # --- Goods List ---
    ttk.Label(parent_frame, text="Goods", font=("Arial", 12, "bold")).grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
    _create_goods_treeview(parent_frame, app)
    app.goods_tree.grid(row=3, column=0, sticky="ewns")
    goods_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.goods_tree.yview)
    app.goods_tree.configure(yscrollcommand=goods_scrollbar.set); goods_scrollbar.grid(row=3, column=1, sticky="ns")
    app.goods_tree.bind("<<TreeviewSelect>>", lambda event: _on_good_select(event, app))

    # --- Recipe Details ---
    ttk.Label(parent_frame, text="Recipe Details", font=("Arial", 12, "bold")).grid(row=4, column=0, sticky=tk.W, pady=(10, 5))
    app.recipe_text = tk.Text(parent_frame, wrap=tk.WORD, state=tk.DISABLED, height=6,
                               bg=DARK_BG, fg=DARK_FG, insertbackground=DARK_INSERT_BG,
                               borderwidth=1, relief=tk.SUNKEN)
    recipe_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.recipe_text.yview)
    app.recipe_text.config(yscrollcommand=recipe_scrollbar.set); app.recipe_text.grid(row=5, column=0, sticky="ewns")
    recipe_scrollbar.grid(row=5, column=1, sticky="ns"); _update_recipe_display(app, "(Select a good)")

    # --- Global Goods Totals ---
    ttk.Label(parent_frame, text="Global Totals", font=("Arial", 12, "bold")).grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
    gt_cols = ["good", "total_qty"]; gt_names = ["Good", "Total Qty"]
    app.global_totals_tree = ttk.Treeview(parent_frame, columns=gt_cols, show="headings", height=4)
    for col, name in zip(gt_cols, gt_names):
        app.global_totals_tree.heading(col, text=name); width = 120; anchor = tk.W
        if col == "total_qty": width = 80; anchor = tk.E
        app.global_totals_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    app.global_totals_tree.grid(row=7, column=0, sticky="ewns")
    gt_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.global_totals_tree.yview)
    app.global_totals_tree.configure(yscrollcommand=gt_scrollbar.set); gt_scrollbar.grid(row=7, column=1, sticky="ns")

    # --- Global Average Prices ---
    ttk.Label(parent_frame, text="Global Average Prices", font=("Arial", 12, "bold")).grid(row=8, column=0, sticky=tk.W, pady=(10, 5))
    avg_price_cols = ["good", "avg_price"]; avg_price_names = ["Good", "Avg Price"]
    app.avg_prices_tree = ttk.Treeview(parent_frame, columns=avg_price_cols, show="headings", height=4)
    for col, name in zip(avg_price_cols, avg_price_names):
        app.avg_prices_tree.heading(col, text=name); width = 120; anchor = tk.W
        if col == "avg_price": width = 80; anchor = tk.E
        app.avg_prices_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    app.avg_prices_tree.grid(row=9, column=0, sticky="ewns")
    avg_prices_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.avg_prices_tree.yview)
    app.avg_prices_tree.configure(yscrollcommand=avg_prices_scrollbar.set); avg_prices_scrollbar.grid(row=9, column=1, sticky="ns")

    # --- NEW: Global Trade Volume ---
    ttk.Label(parent_frame, text="Global Trade Volume", font=("Arial", 12, "bold")).grid(row=10, column=0, sticky=tk.W, pady=(10, 5))
    trade_vol_cols = ["good", "trade_count"]; trade_vol_names = ["Good", "# Trades"]
    app.trade_volume_tree = ttk.Treeview(parent_frame, columns=trade_vol_cols, show="headings", height=4)
    for col, name in zip(trade_vol_cols, trade_vol_names):
        app.trade_volume_tree.heading(col, text=name); width = 120; anchor = tk.W
        if col == "trade_count": width = 80; anchor = tk.E # Right-align count
        app.trade_volume_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    app.trade_volume_tree.grid(row=11, column=0, sticky="ewns")
    trade_vol_scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=app.trade_volume_tree.yview)
    app.trade_volume_tree.configure(yscrollcommand=trade_vol_scrollbar.set); trade_vol_scrollbar.grid(row=11, column=1, sticky="ns")


def update_static_pane(app):
    """Updates the widgets in the static pane."""
    _create_settlements_treeview(app)
    _update_global_totals_display(app)
    _update_global_avg_prices_display(app)
    # NEW: Update trade volume display
    _update_global_trade_volume_display(app)


def _create_settlements_treeview(app):
    """(Re)Creates and populates the static settlements list treeview."""
    if hasattr(app, 'settlements_tree') and app.settlements_tree and app.settlements_tree.winfo_exists():
        selected_id = app.settlements_tree.focus()
        app.settlements_tree.delete(*app.settlements_tree.get_children())
        for settlement in app.settlements:
            pop_display = int(round(settlement.population))
            name_display = f"{settlement.name}{' (A)' if settlement.is_abandoned else ''}"
            values = [settlement.id, name_display, settlement.terrain_type, pop_display]
            try: app.settlements_tree.insert("", tk.END, iid=settlement.id, values=values)
            except tk.TclError: pass
        if selected_id and app.settlements_tree.exists(selected_id):
            app.settlements_tree.focus(selected_id)
            app.settlements_tree.selection_set(selected_id)


def _create_goods_treeview(parent, app):
    """Creates and populates the static goods list treeview."""
    columns = ["id", "name", "base_value", "producible"]; column_names = ["ID", "Name", "Base Val", "Prod?"]
    app.goods_tree = ttk.Treeview(parent, columns=columns, show="headings", height=6)
    for col, name in zip(columns, column_names):
        app.goods_tree.heading(col, text=name); width = 80; anchor = tk.W
        if col == "base_value": anchor = tk.E
        app.goods_tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    for good in app.sorted_goods:
        values = [good.id, good.name, f"{good.base_value:.1f}", "Yes" if good.is_producible else "No"]
        app.goods_tree.insert("", tk.END, iid=good.id, values=values)

def _on_good_select(event, app):
    """Callback function when a good is selected in the goods_tree."""
    if not hasattr(app, 'goods_tree') or not app.goods_tree.winfo_exists(): return
    selected_items = app.goods_tree.selection()
    if not selected_items: _update_recipe_display(app, "(Select a good)"); return

    selected_good = app.world.goods.get(selected_items[0])
    if selected_good and selected_good.recipe:
        recipe = selected_good.recipe; recipe_str = f"** {selected_good.name} ({selected_good.id}) **\n"
        inputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['inputs'].items()]) if recipe['inputs'] else "None"; recipe_str += f"  Inputs: {inputs_str}\n"
        outputs_str = ", ".join([f"{qty} {gid}" for gid, qty in recipe['outputs'].items()]); recipe_str += f"  Outputs: {outputs_str}\n"; recipe_str += f"  Labor: {recipe['labor']:.1f}\n"
        if recipe['wealth_cost'] > 0: recipe_str += f"  Wealth Cost: {recipe['wealth_cost']:.1f}\n"
        if recipe['required_terrain']: recipe_str += f"  Requires: {', '.join(recipe['required_terrain'])}\n"
        _update_recipe_display(app, recipe_str)
    elif selected_good: _update_recipe_display(app, f"** {selected_good.name} ({selected_good.id}) **\n\n(Not producible)")
    else: _update_recipe_display(app, "(Error: Good not found)")

def _update_recipe_display(app, text_content):
    """Updates the content of the recipe details text area."""
    if hasattr(app, 'recipe_text') and app.recipe_text.winfo_exists():
        app.recipe_text.config(state=tk.NORMAL); app.recipe_text.delete('1.0', tk.END)
        app.recipe_text.insert(tk.END, text_content); app.recipe_text.config(state=tk.DISABLED)

def _update_global_totals_display(app):
    """Updates the global goods total treeview in the static pane."""
    if hasattr(app, 'global_totals_tree') and app.global_totals_tree.winfo_exists():
        app.global_totals_tree.delete(*app.global_totals_tree.get_children())
        global_totals = app.world.get_global_good_totals()
        sorted_good_ids = sorted(global_totals.keys(), key=lambda gid: app.world.goods.get(gid, Good(gid,"?",0)).name)
        for good_id in sorted_good_ids:
            good = app.world.goods.get(good_id)
            if not good: continue
            good_name = good.name
            total_qty = global_totals[good_id]
            values = [good_name, f"{total_qty:.1f}"]
            try: app.global_totals_tree.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting global total for {good_name}: {e}")

def _update_global_avg_prices_display(app):
    """Updates the global average prices treeview in the static pane."""
    if hasattr(app, 'avg_prices_tree') and app.avg_prices_tree.winfo_exists():
        app.avg_prices_tree.delete(*app.avg_prices_tree.get_children())
        avg_prices = app.world.get_global_average_prices()
        sorted_good_ids = sorted(avg_prices.keys(), key=lambda gid: app.world.goods.get(gid, Good(gid,"?",0)).name)
        for good_id in sorted_good_ids:
            good = app.world.goods.get(good_id)
            if not good: continue
            good_name = good.name
            avg_price = avg_prices[good_id]
            values = [good_name, f"{avg_price:.2f}"]
            try: app.avg_prices_tree.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting avg price for {good_name}: {e}")

# --- NEW: Update Global Trade Volume ---
def _update_global_trade_volume_display(app):
    """Updates the global trade volume treeview in the static pane."""
    if hasattr(app, 'trade_volume_tree') and app.trade_volume_tree.winfo_exists():
        app.trade_volume_tree.delete(*app.trade_volume_tree.get_children())
        trade_counts = app.world.global_trade_counts # Get data from world

        # Sort by good name using app's world.goods dictionary
        sorted_good_ids = sorted(trade_counts.keys(), key=lambda gid: app.world.goods.get(gid, Good(gid,"?",0)).name) # Safer sort

        for good_id in sorted_good_ids:
            good = app.world.goods.get(good_id)
            if not good: continue # Skip if good somehow doesn't exist
            good_name = good.name
            count = trade_counts[good_id]
            values = [good_name, f"{count}"] # Display count as integer
            try: app.trade_volume_tree.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting trade volume for {good_name}: {e}")

