import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont

def setup_dynamic_pane(parent_frame, app):
    """
    Sets up the scrollable area for the 'Settlement Details' tab.

    Args:
        parent_frame (ttk.Frame): The parent frame for this pane (the tab).
        app (SimulationUI): The main application instance.
    """
    DARK_BG = app.root.cget('bg')

    # --- Create Scrollable Area ---
    app.scrollable_canvas = tk.Canvas(parent_frame, bg=DARK_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=app.scrollable_canvas.yview)
    app.scrollable_frame = ttk.Frame(app.scrollable_canvas)

    app.scrollable_canvas.configure(yscrollcommand=scrollbar.set)
    app.scrollable_canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    app.canvas_frame_id = app.scrollable_canvas.create_window((0, 0), window=app.scrollable_frame, anchor="nw")

    app.scrollable_frame.bind("<Configure>", lambda e: _on_frame_configure(e, app))
    app.scrollable_canvas.bind("<Configure>", lambda e: _on_canvas_configure(e, app))
    app.scrollable_canvas.bind("<MouseWheel>", lambda e: _on_mousewheel(e, app))
    app.scrollable_canvas.bind("<Button-4>", lambda e: _on_mousewheel(e, app))
    app.scrollable_canvas.bind("<Button-5>", lambda e: _on_mousewheel(e, app))


def update_dynamic_pane(app):
    """
    Optimized update for the dynamic settlement details pane.
    Creates/destroys widgets only when settlements are added/removed.
    Updates content of existing widgets otherwise. Handles abandoned status.

    Args:
        app (SimulationUI): The main application instance.
    """
    if not hasattr(app, 'scrollable_frame') or not app.scrollable_frame.winfo_exists():
        print("WARN: Scrollable frame not ready for dynamic update.")
        return

    current_settlement_ids = set(s.id for s in app.settlements)
    existing_widget_ids = set(app.settlement_widgets.keys())

    # --- Remove Widgets for Deleted Settlements ---
    ids_to_remove = existing_widget_ids - current_settlement_ids
    for settlement_id in ids_to_remove:
        if settlement_id in app.settlement_widgets:
            try: app.settlement_widgets[settlement_id]['frame'].destroy()
            except tk.TclError: print(f"WARN: TclError destroying frame for removed settlement {settlement_id}")
            del app.settlement_widgets[settlement_id]

    # --- Add/Update Widgets for Current Settlements ---
    row_index = 0
    for settlement in app.settlements:
        settlement_id = settlement.id
        if settlement_id not in app.settlement_widgets:
            app.settlement_widgets[settlement_id] = _create_settlement_detail_widgets(app.scrollable_frame, settlement, app)
            app.settlement_widgets[settlement_id]['frame'].grid(row=row_index, column=0, sticky="ew", padx=5, pady=(0, 10))
            app.scrollable_frame.columnconfigure(0, weight=1)

        if settlement_id in app.settlement_widgets:
             _update_settlement_detail_widgets(settlement, app.settlement_widgets[settlement_id], app)
             app.settlement_widgets[settlement_id]['frame'].grid(row=row_index, column=0, sticky="ew", padx=5, pady=(0, 10))
             row_index += 1

    app.scrollable_frame.update_idletasks()
    _on_frame_configure(None, app)

# --- Helper Functions for Dynamic Widgets ---

def _create_settlement_detail_widgets(parent_frame, settlement, app):
    """
    Creates the widgets (Labels, Treeviews) for a single settlement's detail view.
    Includes internal state variables.
    """
    widgets = {}
    title_suffix = " (Abandoned)" if settlement.is_abandoned else ""
    frame = ttk.LabelFrame(parent_frame, text=f"{settlement.name} ({settlement.id}){title_suffix}", padding=5)
    widgets['frame'] = frame

    # Configure grid columns inside the LabelFrame (Back to 4 columns)
    frame.columnconfigure(1, weight=0, minsize=80)  # Value column
    frame.columnconfigure(2, weight=1, minsize=120) # Inventory tree
    frame.columnconfigure(3, weight=1, minsize=100) # Production tree

    # --- Create Labels for basic stats ---
    label_width = 12
    widgets['pop_label_title'] = ttk.Label(frame, text="Population:")
    widgets['pop_label_value'] = ttk.Label(frame, text="0", width=label_width, anchor="e")
    widgets['wealth_label_title'] = ttk.Label(frame, text="Wealth:")
    widgets['wealth_label_value'] = ttk.Label(frame, text="0.0", width=label_width, anchor="e")
    widgets['labor_label_title'] = ttk.Label(frame, text="Labor:")
    widgets['labor_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=label_width, anchor="e")
    widgets['storage_label_title'] = ttk.Label(frame, text="Storage:")
    widgets['storage_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=label_width, anchor="e")
    widgets['market_level_title'] = ttk.Label(frame, text="Market Lvl:")
    widgets['market_level_value'] = ttk.Label(frame, text="1", width=label_width, anchor="e")
    widgets['trade_capacity_title'] = ttk.Label(frame, text="Trades (Tick):")
    widgets['trade_capacity_value'] = ttk.Label(frame, text="0/0", width=label_width, anchor="e")
    widgets['total_trades_title'] = ttk.Label(frame, text="Total Trades:")
    widgets['total_trades_value'] = ttk.Label(frame, text="0", width=label_width, anchor="e")
    # NEW: Internal State Labels
    widgets['food_ticks_title'] = ttk.Label(frame, text="Food Ticks:")
    widgets['food_ticks_value'] = ttk.Label(frame, text="0", width=label_width, anchor="e")
    widgets['wealth_ticks_title'] = ttk.Label(frame, text="Wealth Ticks:")
    widgets['wealth_ticks_value'] = ttk.Label(frame, text="0", width=label_width, anchor="e")
    widgets['needs_title'] = ttk.Label(frame, text="Elevated Needs:")
    # Use wraplength for the needs label as it might get long
    widgets['needs_value'] = ttk.Label(frame, text="(None)", anchor="nw", justify=tk.LEFT, wraplength=180) # Adjust wraplength as needed

    # --- Grid Labels ---
    row_offset = 0
    widgets['pop_label_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['pop_label_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['wealth_label_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['wealth_label_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['labor_label_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['labor_label_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['storage_label_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['storage_label_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['market_level_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['market_level_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['trade_capacity_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['trade_capacity_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['total_trades_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['total_trades_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    # Grid Internal State Labels
    widgets['food_ticks_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['food_ticks_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    widgets['wealth_ticks_title'].grid(row=row_offset, column=0, sticky="w")
    widgets['wealth_ticks_value'].grid(row=row_offset, column=1, sticky="e", padx=(0,5))
    row_offset += 1
    # Grid Needs Label (spans 2 columns for text)
    widgets['needs_title'].grid(row=row_offset, column=0, sticky="nw", pady=(2,0))
    widgets['needs_value'].grid(row=row_offset, column=1, columnspan=2, sticky="nsew", pady=(2,0)) # Span columns 1 and 2


    # --- Create Treeviews ---
    tree_rows = row_offset + 1 # Update total rows used by labels
    # Inventory
    inv_cols = ["good", "price", "stock"]; inv_names = ["Inventory", "Price", "Stock"]
    inv_tree = ttk.Treeview(frame, columns=inv_cols, show="headings", height=tree_rows)
    inv_tree.grid(row=0, column=2, rowspan=tree_rows, sticky="nsew", padx=(10, 0)) # Grid in column 2
    inv_tree.heading("good", text=inv_names[0]); inv_tree.column("good", width=60, anchor=tk.W, stretch=tk.NO)
    inv_tree.heading("price", text=inv_names[1]); inv_tree.column("price", width=40, anchor=tk.E, stretch=tk.NO)
    inv_tree.heading("stock", text=inv_names[2]); inv_tree.column("stock", width=40, anchor=tk.E, stretch=tk.NO)
    widgets['inv_tree'] = inv_tree

    # Production
    prod_cols = ["good", "produced"]; prod_names = ["Produced", "Qty"]
    prod_tree = ttk.Treeview(frame, columns=prod_cols, show="headings", height=tree_rows)
    prod_tree.grid(row=0, column=3, rowspan=tree_rows, sticky="nsew", padx=(5, 0)) # Grid in column 3
    prod_tree.heading("good", text=prod_names[0]); prod_tree.column("good", width=60, anchor=tk.W, stretch=tk.NO)
    prod_tree.heading("produced", text=prod_names[1]); prod_tree.column("produced", width=40, anchor=tk.E, stretch=tk.NO)
    widgets['prod_tree'] = prod_tree

    # Removed Needs Treeview creation

    return widgets

def _update_settlement_detail_widgets(settlement, widgets, app):
    """
    Updates the content of the widgets for a single settlement's detail view.
    Handles abandoned status display and internal variables.
    """
    title_suffix = " (Abandoned)" if settlement.is_abandoned else ""
    widgets['frame'].config(text=f"{settlement.name} ({settlement.id}){title_suffix}")

    # Update Labels
    widgets['pop_label_value'].config(text=f"{int(round(settlement.population))}")
    widgets['wealth_label_value'].config(text=f"{settlement.wealth:,.1f}")
    widgets['labor_label_value'].config(text=f"{settlement.current_labor_pool:.1f} / {settlement.max_labor_pool:.1f}")
    storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
    widgets['storage_label_value'].config(text=f"{storage_load:.1f} / {storage_cap:.0f}")
    widgets['market_level_value'].config(text=f"{settlement.market_level}")
    widgets['trade_capacity_value'].config(text=f"{settlement.trades_executed_this_tick} / {settlement.trade_capacity}")
    widgets['total_trades_value'].config(text=f"{settlement.total_trades_completed}")
    # Update Internal State Labels
    widgets['food_ticks_value'].config(text=f"{settlement.ticks_below_food_threshold}")
    widgets['wealth_ticks_value'].config(text=f"{settlement.ticks_below_wealth_threshold}")

    # --- Update Treeviews (Clear if abandoned) ---
    inv_tree = widgets['inv_tree']
    prod_tree = widgets['prod_tree']
    inv_tree.delete(*inv_tree.get_children())
    prod_tree.delete(*prod_tree.get_children())

    # --- Update Needs Label ---
    needs_str_list = []
    if not settlement.is_abandoned:
        sorted_need_ids = sorted(settlement.consumption_needs.keys(), key=lambda gid: app.world.goods.get(gid, None).name if app.world.goods.get(gid) else "")
        for good_id in sorted_need_ids:
            need_multiplier = settlement.consumption_needs[good_id]
            if need_multiplier > 1.01:
                 good = app.world.goods.get(good_id)
                 if good: needs_str_list.append(f"{good.name}: {need_multiplier:.2f}x")
        needs_display_text = ", ".join(needs_str_list) if needs_str_list else "(None)"
    else:
        needs_display_text = "(Abandoned)"
    widgets['needs_value'].config(text=needs_display_text)


    # --- Populate Trees if not abandoned ---
    if not settlement.is_abandoned:
        # Update Inventory Treeview
        for good in app.sorted_goods:
            stock = settlement.get_total_stored(good.id)
            if stock > 1e-6:
                price = settlement.local_prices.get(good.id)
                price_str = f"{price:.2f}" if price is not None else "N/A"
                stock_str = f"{stock:.1f}"
                try: inv_tree.insert("", tk.END, values=(good.name, price_str, stock_str))
                except Exception as e: print(f"Error inserting inv item {good.name}: {e}")

        # Update Production Treeview
        if settlement.production_this_tick:
             sorted_prod_ids = sorted(settlement.production_this_tick.keys(), key=lambda gid: app.world.goods[gid].name)
             for good_id in sorted_prod_ids:
                 produced_qty = settlement.production_this_tick[good_id]
                 if produced_qty > 1e-6:
                     good_name = app.world.goods[good_id].name
                     try: prod_tree.insert("", tk.END, values=(good_name, f"{produced_qty:.1f}"))
                     except Exception as e: print(f"Error inserting prod item {good_name}: {e}")
        else:
            try: prod_tree.insert("", tk.END, values=("(None)", "-"))
            except Exception as e: print(f"Error inserting prod none: {e}")
    else:
        # Display "(Abandoned)" in treeviews
        try: inv_tree.insert("", tk.END, values=("(Abandoned)", "-", "-"))
        except Exception as e: print(f"Error inserting inv abandoned: {e}")
        try: prod_tree.insert("", tk.END, values=("(Abandoned)", "-"))
        except Exception as e: print(f"Error inserting prod abandoned: {e}")


# --- Scrollable Frame Helper Methods ---
def _on_frame_configure(event, app):
    """Updates the scroll region when the inner frame size changes."""
    if hasattr(app, 'scrollable_canvas') and app.scrollable_canvas.winfo_exists():
         app.scrollable_canvas.configure(scrollregion=app.scrollable_canvas.bbox("all"))

def _on_canvas_configure(event, app):
    """Adjusts the width of the inner frame to match the canvas width."""
    if hasattr(app, 'scrollable_canvas') and hasattr(app, 'canvas_frame_id') and app.scrollable_canvas.winfo_exists():
        canvas_width = event.width
        app.scrollable_canvas.itemconfig(app.canvas_frame_id, width=canvas_width)

def _on_mousewheel(event, app):
    """Handles mouse wheel scrolling for the canvas."""
    if hasattr(app, 'scrollable_canvas') and app.scrollable_canvas.winfo_exists():
        if event.num == 5 or event.delta < 0: app.scrollable_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0: app.scrollable_canvas.yview_scroll(-1, "units")
# --- End Scrollable Frame Helpers ---
