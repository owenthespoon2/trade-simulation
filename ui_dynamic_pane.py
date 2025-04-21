import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont # Keep if needed

# Assuming colors are defined in ui_main or passed via app instance
# DARK_BG = "#2e2e2e" # Example

def setup_dynamic_pane(parent_frame, app):
    """
    Sets up the scrollable area for the 'Settlement Details' tab.

    Args:
        parent_frame (ttk.Frame): The parent frame for this pane (the tab).
        app (SimulationUI): The main application instance.
    """
    # Access theme colors from the app instance if needed
    DARK_BG = app.root.cget('bg')

    # --- Create Scrollable Area ---
    app.scrollable_canvas = tk.Canvas(parent_frame, bg=DARK_BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=app.scrollable_canvas.yview)
    app.scrollable_frame = ttk.Frame(app.scrollable_canvas) # Use app instance to store ref

    app.scrollable_canvas.configure(yscrollcommand=scrollbar.set)
    app.scrollable_canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")
    app.canvas_frame_id = app.scrollable_canvas.create_window((0, 0), window=app.scrollable_frame, anchor="nw")

    # Bind events using methods defined within this module or passed from app
    app.scrollable_frame.bind("<Configure>", lambda e: _on_frame_configure(e, app))
    app.scrollable_canvas.bind("<Configure>", lambda e: _on_canvas_configure(e, app))
    # Bind mouse wheel - might need adjustment depending on how app handles root binding
    # Binding directly to canvas might be better than bind_all
    app.scrollable_canvas.bind("<MouseWheel>", lambda e: _on_mousewheel(e, app)) # Windows/macOS
    app.scrollable_canvas.bind("<Button-4>", lambda e: _on_mousewheel(e, app)) # Linux scroll up
    app.scrollable_canvas.bind("<Button-5>", lambda e: _on_mousewheel(e, app)) # Linux scroll down


def update_dynamic_pane(app):
    """
    Optimized update for the dynamic settlement details pane.
    Creates/destroys widgets only when settlements are added/removed.
    Updates content of existing widgets otherwise.

    Args:
        app (SimulationUI): The main application instance.
    """
    # Check if the necessary container widgets exist
    if not hasattr(app, 'scrollable_frame') or not app.scrollable_frame.winfo_exists():
        print("WARN: Scrollable frame not ready for dynamic update.")
        return

    current_settlement_ids = set(s.id for s in app.settlements)
    existing_widget_ids = set(app.settlement_widgets.keys())

    # --- Remove Widgets for Abandoned Settlements ---
    ids_to_remove = existing_widget_ids - current_settlement_ids
    for settlement_id in ids_to_remove:
        if settlement_id in app.settlement_widgets:
            try:
                # Destroy the main frame for the settlement, which should destroy children
                app.settlement_widgets[settlement_id]['frame'].destroy()
            except tk.TclError:
                print(f"WARN: TclError destroying frame for removed settlement {settlement_id}")
            # Remove the entry from the tracking dictionary
            del app.settlement_widgets[settlement_id]

    # --- Add/Update Widgets for Current Settlements ---
    row_index = 0
    for settlement in app.settlements:
        settlement_id = settlement.id

        if settlement_id not in app.settlement_widgets:
            # --- Create Widgets for New Settlement ---
            # Call helper function to create the widget structure
            app.settlement_widgets[settlement_id] = _create_settlement_detail_widgets(app.scrollable_frame, settlement, app)
            # Grid the new frame immediately
            app.settlement_widgets[settlement_id]['frame'].grid(row=row_index, column=0, sticky="ew", padx=5, pady=(0, 10))
            # Configure column weight for the scrollable frame
            app.scrollable_frame.columnconfigure(0, weight=1)

        # --- Update Existing Widgets ---
        # Call helper function to update the content of the widgets
        _update_settlement_detail_widgets(settlement, app.settlement_widgets[settlement_id], app)

        # Ensure the updated/new frame is at the correct row
        # Re-gridding ensures order if settlements list changes order (unlikely now but safer)
        if settlement_id in app.settlement_widgets: # Check if creation succeeded
             app.settlement_widgets[settlement_id]['frame'].grid(row=row_index, column=0, sticky="ew", padx=5, pady=(0, 10))
             row_index += 1


    # Update scroll region after potential changes
    # Use update_idletasks to ensure geometry is updated before getting bbox
    app.scrollable_frame.update_idletasks()
    _on_frame_configure(None, app) # Manually trigger scroll region update

# --- Helper Functions for Dynamic Widgets ---

def _create_settlement_detail_widgets(parent_frame, settlement, app):
    """
    Creates the widgets (Labels, Treeviews) for a single settlement's detail view.

    Args:
        parent_frame (ttk.Frame): The frame to place these widgets into (the scrollable frame).
        settlement (Settlement): The settlement object.
        app (SimulationUI): The main application instance.

    Returns:
        dict: A dictionary containing references to the created widgets for this settlement.
    """
    widgets = {}
    # Create the main container frame for this settlement
    frame = ttk.LabelFrame(parent_frame, text=f"{settlement.name} ({settlement.id})", padding=5)
    widgets['frame'] = frame

    # Configure grid columns inside the LabelFrame
    frame.columnconfigure(1, weight=0, minsize=70) # Column for values - give minsize
    frame.columnconfigure(2, weight=1, minsize=150) # Inventory tree
    frame.columnconfigure(3, weight=1, minsize=100) # Production tree

    # Create Labels for basic stats
    widgets['pop_label_title'] = ttk.Label(frame, text="Population:")
    widgets['pop_label_value'] = ttk.Label(frame, text="0", width=6, anchor="e") # Fixed width
    widgets['wealth_label_title'] = ttk.Label(frame, text="Wealth:")
    widgets['wealth_label_value'] = ttk.Label(frame, text="0.0", width=8, anchor="e") # Fixed width
    widgets['labor_label_title'] = ttk.Label(frame, text="Labor:")
    widgets['labor_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=10, anchor="e") # Fixed width
    widgets['storage_label_title'] = ttk.Label(frame, text="Storage:")
    widgets['storage_label_value'] = ttk.Label(frame, text="0.0 / 0.0", width=12, anchor="e") # Fixed width

    # Grid Labels
    widgets['pop_label_title'].grid(row=0, column=0, sticky="w")
    widgets['pop_label_value'].grid(row=0, column=1, sticky="e", padx=(0,5)) # Align right, add padding
    widgets['wealth_label_title'].grid(row=1, column=0, sticky="w")
    widgets['wealth_label_value'].grid(row=1, column=1, sticky="e", padx=(0,5))
    widgets['labor_label_title'].grid(row=2, column=0, sticky="w")
    widgets['labor_label_value'].grid(row=2, column=1, sticky="e", padx=(0,5))
    widgets['storage_label_title'].grid(row=3, column=0, sticky="w")
    widgets['storage_label_value'].grid(row=3, column=1, sticky="e", padx=(0,5))

    # Create Inventory Treeview
    inv_cols = ["good", "price", "stock"]; inv_names = ["Inventory", "Price", "Stock"]
    inv_tree = ttk.Treeview(frame, columns=inv_cols, show="headings", height=4) # Fixed height
    inv_tree.grid(row=0, column=2, rowspan=4, sticky="nsew", padx=(10, 0)) # Padding added
    inv_tree.heading("good", text=inv_names[0]); inv_tree.column("good", width=70, anchor=tk.W, stretch=tk.NO)
    inv_tree.heading("price", text=inv_names[1]); inv_tree.column("price", width=40, anchor=tk.E, stretch=tk.NO)
    inv_tree.heading("stock", text=inv_names[2]); inv_tree.column("stock", width=40, anchor=tk.E, stretch=tk.NO)
    widgets['inv_tree'] = inv_tree

    # Create Production Treeview
    prod_cols = ["good", "produced"]; prod_names = ["Produced", "Qty"]
    prod_tree = ttk.Treeview(frame, columns=prod_cols, show="headings", height=4) # Fixed height
    prod_tree.grid(row=0, column=3, rowspan=4, sticky="nsew", padx=(5, 0))
    prod_tree.heading("good", text=prod_names[0]); prod_tree.column("good", width=70, anchor=tk.W, stretch=tk.NO)
    prod_tree.heading("produced", text=prod_names[1]); prod_tree.column("produced", width=40, anchor=tk.E, stretch=tk.NO)
    widgets['prod_tree'] = prod_tree

    # Add small scrollbars to treeviews if desired (optional)
    # inv_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=inv_tree.yview)
    # inv_tree.configure(yscrollcommand=inv_scrollbar.set)
    # inv_scrollbar.grid(row=0, column=2, rowspan=4, sticky='nse', padx=(0, 5)) # Adjust grid position

    return widgets

def _update_settlement_detail_widgets(settlement, widgets, app):
    """
    Updates the content of the widgets for a single settlement's detail view.

    Args:
        settlement (Settlement): The settlement object with current data.
        widgets (dict): The dictionary containing references to this settlement's widgets.
        app (SimulationUI): The main application instance (to access world.goods).
    """
    # Update Labels
    widgets['pop_label_value'].config(text=f"{int(round(settlement.population))}")
    widgets['wealth_label_value'].config(text=f"{settlement.wealth:.1f}")
    widgets['labor_label_value'].config(text=f"{settlement.current_labor_pool:.1f}/{settlement.max_labor_pool:.1f}")
    storage_load = settlement.get_current_storage_load(); storage_cap = settlement.storage_capacity
    widgets['storage_label_value'].config(text=f"{storage_load:.1f}/{storage_cap:.0f}")

    # Update Inventory Treeview
    inv_tree = widgets['inv_tree']
    inv_tree.delete(*inv_tree.get_children()) # Clear existing rows
    # Use app.sorted_goods for consistent order and access to names
    for good in app.sorted_goods:
        stock = settlement.get_total_stored(good.id)
        if stock > 1e-6: # Only show goods the settlement has
            price = settlement.local_prices.get(good.id)
            price_str = f"{price:.2f}" if price is not None else "N/A"
            stock_str = f"{stock:.1f}"
            try: inv_tree.insert("", tk.END, values=(good.name, price_str, stock_str))
            except Exception as e: print(f"Error inserting inv item {good.name}: {e}")

    # Update Production Treeview
    prod_tree = widgets['prod_tree']
    prod_tree.delete(*prod_tree.get_children()) # Clear existing rows
    if settlement.production_this_tick:
         # Sort by good name using app.world.goods
         sorted_prod_ids = sorted(settlement.production_this_tick.keys(), key=lambda gid: app.world.goods[gid].name)
         for good_id in sorted_prod_ids:
             produced_qty = settlement.production_this_tick[good_id]
             if produced_qty > 1e-6:
                 good_name = app.world.goods[good_id].name
                 try: prod_tree.insert("", tk.END, values=(good_name, f"{produced_qty:.1f}"))
                 except Exception as e: print(f"Error inserting prod item {good_name}: {e}")
    else:
        # Indicate no production if dictionary is empty
        try: prod_tree.insert("", tk.END, values=("(None)", "-"))
        except Exception as e: print(f"Error inserting prod none: {e}")


# --- Scrollable Frame Helper Methods --- (Copied from original trade_ui.py)
# These need access to the app instance to find the canvas/frame
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
        # Determine scroll direction and amount based on platform
        if event.num == 5 or event.delta < 0: # Scroll down
            app.scrollable_canvas.yview_scroll(1, "units")
        elif event.num == 4 or event.delta > 0: # Scroll up
            app.scrollable_canvas.yview_scroll(-1, "units")
# --- End Scrollable Frame Helpers ---

