import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import math
import random
import traceback # Added for error printing
from trade_logic import Good # <--- IMPORT ADDED HERE

def setup_map_pane(parent_frame, app):
    """
    Sets up the widgets for the 'Map' tab (canvas, info labels, legend).
    Note: parent_frame is now the main frame for the Map tab, which is
          configured with 2 columns (0 for map, 1 for legend).

    Args:
        parent_frame (ttk.Frame): The parent frame for this pane (the tab).
        app (SimulationUI): The main application instance.
    """
    # --- Map Canvas (Column 0) ---
    map_canvas_frame = ttk.Frame(parent_frame) # Frame to hold canvas and label
    map_canvas_frame.grid(row=0, column=0, rowspan=3, sticky="nsew") # Span rows, stick to all sides
    map_canvas_frame.rowconfigure(1, weight=1)
    map_canvas_frame.columnconfigure(0, weight=1)

    ttk.Label(map_canvas_frame, text="Trade Map", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
    app.map_canvas = tk.Canvas(map_canvas_frame, bg=app.CANVAS_BG, width=500, height=400, highlightthickness=0)
    app.map_canvas.grid(row=1, column=0, sticky="nsew")

    # Info Frame (Below Map Canvas in Column 0)
    info_frame = ttk.LabelFrame(map_canvas_frame, text="Last Trade Details (This Tick)", padding="5")
    info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    info_frame.columnconfigure(0, weight=1)
    last_trade_label = ttk.Label(info_frame, textvariable=app.last_trade_info_var, wraplength=450)
    last_trade_label.grid(row=0, column=0, sticky=tk.W)
    last_trade_reason_label = ttk.Label(info_frame, textvariable=app.last_trade_reason_var)
    last_trade_reason_label.grid(row=1, column=0, sticky=tk.W)

    # --- Legend (Column 1) ---
    legend_container = ttk.Frame(parent_frame, padding=(5, 0))
    legend_container.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(5,0)) # Place in column 1, stick vertically
    legend_container.rowconfigure(1, weight=0) # Label row
    legend_container.rowconfigure(2, weight=1) # Legend frame row (allow expansion if needed)

    ttk.Label(legend_container, text="Goods Key", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.NW, pady=(0,5))
    # Create a frame specifically for the legend items, store on app
    app.goods_legend_frame = ttk.Frame(legend_container)
    app.goods_legend_frame.grid(row=1, column=0, sticky="nsew")

    # Populate the legend initially
    _update_goods_legend(app)


def update_map_pane(app):
    """
    Updates the map visualization: settlement visuals and moving shipment markers.

    Args:
        app (SimulationUI): The main application instance.
    """
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return

    # 1. Update Settlement Visuals (Size/Color)
    _update_settlement_visuals(app)

    # 2. Update "Last Trade Details" Label based on trades initiated this tick
    last_trade_details = None
    trades_this_tick = list(app.world.executed_trade_details_this_tick)
    if trades_this_tick:
        last_trade_details = trades_this_tick[-1] # Get the last initiated trade
    else:
        if hasattr(app, 'last_trade_info_var'): app.last_trade_info_var.set("No trades initiated this tick.")
        if hasattr(app, 'last_trade_reason_var'): app.last_trade_reason_var.set("")

    if last_trade_details:
        goods_cost = last_trade_details['quantity'] * last_trade_details['seller_price']
        transport_cost = last_trade_details.get('transport_cost_total', 0.0)
        eta_tick = last_trade_details.get('arrival_tick', '?')
        info = (f"Trade Sent: {last_trade_details['quantity']:.1f} {last_trade_details['good_name']} "
                f"from {last_trade_details['seller_name']} to {last_trade_details['buyer_name']}")
        reason = (f"Reason: Sell P={last_trade_details['seller_price']:.2f}, "
                  f"Buy P={last_trade_details['buyer_price']:.2f} "
                  f"(Pot Profit/U={last_trade_details.get('potential_profit_per_unit', 0.0):.2f}, "
                  f"Goods Cost: {goods_cost:.2f}, TCost: {transport_cost:.2f}, ETA: T{eta_tick})") # Added ETA
        if hasattr(app, 'last_trade_info_var'): app.last_trade_info_var.set(info)
        if hasattr(app, 'last_trade_reason_var'): app.last_trade_reason_var.set(reason)

    # 3. Update Moving Shipment Markers (Color-coded)
    _update_shipment_markers(app)


# --- Visualization Drawing Methods ---

def _calculate_settlement_radius(app, wealth):
    """Calculates settlement radius based on wealth."""
    try: radius_increase = math.sqrt(max(0, wealth)) * app.SETTLEMENT_WEALTH_SCALE_PARAM
    except ValueError: radius_increase = 0
    capped_increase = min(radius_increase, app.SETTLEMENT_MAX_RADIUS_INCREASE)
    return app.SETTLEMENT_BASE_RADIUS + capped_increase

def create_settlement_canvas_items(app):
    """Creates the initial visual representation of settlements."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    app.map_canvas.delete("settlement"); app.settlement_canvas_items.clear()
    for settlement in app.settlements:
        x, y, _ = app.settlement_coords[settlement.id]
        r = app.SETTLEMENT_BASE_RADIUS
        color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR
        circle_id = app.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=app.DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
        text_id = app.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=app.DARK_FG, font=app.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
        wealth_id = app.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=app.WEALTH_TEXT_COLOR, font=app.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
        app.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
    _update_settlement_visuals(app) # Ensure initial size/color is correct

def _update_settlement_visuals(app):
    """Updates existing settlement visuals on the map."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    valid_settlement_ids = set(s.id for s in app.settlements)
    ids_to_remove = set(app.settlement_canvas_items.keys()) - valid_settlement_ids
    for settlement_id in ids_to_remove:
        if settlement_id in app.settlement_canvas_items:
            items = app.settlement_canvas_items[settlement_id]
            for item_key in ['circle', 'text', 'wealth']:
                 if item_key in items: _delete_canvas_item(app, items[item_key])
            del app.settlement_canvas_items[settlement_id]

    for settlement in app.settlements:
        settlement_id = settlement.id; items = app.settlement_canvas_items.get(settlement_id)
        # Check if canvas items still exist before trying to update them
        items_valid = items and all(k in items and app.map_canvas.winfo_exists() and app.map_canvas.find_withtag(items[k]) for k in ['circle', 'text', 'wealth'])
        if items_valid:
            try:
                x, y, _ = app.settlement_coords[settlement.id]; wealth = settlement.wealth
                new_r = _calculate_settlement_radius(app, wealth); circle_id = items['circle']; text_id = items['text']; wealth_id = items['wealth']
                current_color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR
                app.map_canvas.coords(circle_id, x - new_r, y - new_r, x + new_r, y + new_r); app.map_canvas.itemconfig(circle_id, fill=current_color)
                app.map_canvas.coords(text_id, x, y + new_r + 8); app.map_canvas.coords(wealth_id, x, y - new_r - 8)
                app.map_canvas.itemconfig(wealth_id, text=f"W: {wealth:.0f}")
            except tk.TclError as e: print(f"WARN: TclError updating visuals for settlement {settlement_id}: {e}")
            except Exception as e: print(f"ERROR updating visuals for settlement {settlement_id}:"); traceback.print_exc()
        elif settlement_id not in app.settlement_canvas_items:
             # If settlement exists in data but not on canvas, create it
             _create_single_settlement_item(app, settlement)

def _create_single_settlement_item(app, settlement):
    """Creates canvas items for a single new settlement."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    if settlement.id in app.settlement_canvas_items: return # Already exists
    x, y, _ = app.settlement_coords[settlement.id]; r = app.SETTLEMENT_BASE_RADIUS
    color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR
    circle_id = app.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=app.DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
    text_id = app.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=app.DARK_FG, font=app.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
    wealth_id = app.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=app.WEALTH_TEXT_COLOR, font=app.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
    app.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
    _update_settlement_visuals(app) # Call update to set correct radius/color immediately

# REMOVED _draw_trade_route_effect as requested

def _update_shipment_markers(app):
    """Creates, updates positions of, and removes shipment markers on the map, color-coded by good."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return

    current_shipment_ids = set()
    world_tick = app.world.tick

    # Iterate through current shipments in the world state
    for shipment in app.world.in_transit_shipments:
        shipment_id = shipment['shipment_id']
        current_shipment_ids.add(shipment_id)

        # Get coordinates and good color
        seller_coords = app.settlement_coords.get(shipment['seller_id'])
        buyer_coords = app.settlement_coords.get(shipment['buyer_id'])
        good_id = shipment['good_id']
        # Get color from app's map, fallback to default
        marker_color = app.good_colors.get(good_id, app.SHIPMENT_MARKER_COLOR)

        if not seller_coords or not buyer_coords:
            if shipment_id in app.shipment_markers:
                _delete_canvas_item(app, app.shipment_markers[shipment_id])
                del app.shipment_markers[shipment_id]
            continue

        x1, y1, _ = seller_coords
        x2, y2, _ = buyer_coords

        # Calculate progress
        departure_tick = shipment['departure_tick']
        arrival_tick = shipment['arrival_tick']
        total_duration = max(1, arrival_tick - departure_tick) # Avoid division by zero
        ticks_elapsed = world_tick - departure_tick
        progress = max(0.0, min(1.0, ticks_elapsed / total_duration))

        # Calculate current position
        current_x = x1 + (x2 - x1) * progress
        current_y = y1 + (y2 - y1) * progress
        marker_r = app.TRADE_MARKER_RADIUS

        # Check if marker exists
        if shipment_id in app.shipment_markers:
            # Update position and ensure color is correct
            marker_item_id = app.shipment_markers[shipment_id]
            try:
                if app.map_canvas.find_withtag(marker_item_id): # Check if item still exists
                     app.map_canvas.coords(marker_item_id,
                                           current_x - marker_r, current_y - marker_r,
                                           current_x + marker_r, current_y + marker_r)
                     # Update color just in case good definitions change (unlikely now, but safer)
                     app.map_canvas.itemconfig(marker_item_id, fill=marker_color)
                else: # Item was somehow deleted, remove from tracking
                     print(f"WARN: Shipment marker {marker_item_id} for {shipment_id} not found on canvas, removing tracker.")
                     if shipment_id in app.shipment_markers: del app.shipment_markers[shipment_id] # Ensure cleanup
            except tk.TclError:
                 print(f"WARN: TclError updating coords for shipment marker {shipment_id}")
                 if shipment_id in app.shipment_markers: del app.shipment_markers[shipment_id] # Clean up tracker
        else:
            # Create new marker with the correct color
            marker_item_id = app.map_canvas.create_oval(
                current_x - marker_r, current_y - marker_r,
                current_x + marker_r, current_y + marker_r,
                fill=marker_color, # Use good-specific color
                outline="",
                tags=("shipment_marker", shipment_id)
            )
            app.shipment_markers[shipment_id] = marker_item_id

    # Remove markers for shipments that are no longer in transit
    ids_to_remove = set(app.shipment_markers.keys()) - current_shipment_ids
    for shipment_id in ids_to_remove:
        marker_item_id = app.shipment_markers[shipment_id]
        _delete_canvas_item(app, marker_item_id)
        del app.shipment_markers[shipment_id]


def _update_goods_legend(app):
    """Populates the goods legend frame with color squares and names."""
    if not hasattr(app, 'goods_legend_frame') or not app.goods_legend_frame.winfo_exists():
        print("WARN: Legend frame not ready for update.")
        return

    # Clear existing legend items
    for widget in app.goods_legend_frame.winfo_children():
        widget.destroy()

    # Add items based on the good_colors map
    row_index = 0
    # Sort goods by name for consistent legend order
    sorted_good_ids = sorted(app.good_colors.keys(), key=lambda gid: app.world.goods[gid].name)

    for good_id in sorted_good_ids:
        color = app.good_colors.get(good_id, app.SHIPMENT_MARKER_COLOR)
        # FIX: Use the imported Good class for the fallback object
        good_name = app.world.goods.get(good_id, Good(good_id, f"Unknown ({good_id})", 0)).name # Get name safely

        # Create a small colored square (using a Frame)
        color_box = tk.Frame(app.goods_legend_frame, width=10, height=10, bg=color, relief=tk.SOLID, borderwidth=1)
        color_box.grid(row=row_index, column=0, padx=(0, 3), pady=1)

        # Create the label
        label = ttk.Label(app.goods_legend_frame, text=good_name, font=app.legend_font)
        label.grid(row=row_index, column=1, sticky=tk.W)

        row_index += 1


def _set_item_color(app, item_id, color):
    """Safely changes the fill color of a canvas item."""
    try:
        if hasattr(app, 'map_canvas') and app.map_canvas.winfo_exists() and app.map_canvas.find_withtag(item_id):
            app.map_canvas.itemconfig(item_id, fill=color)
    except tk.TclError: pass
def _delete_canvas_item(app, item_id):
    """Safely deletes a canvas item."""
    try:
        if hasattr(app, 'map_canvas') and app.map_canvas.winfo_exists() and app.map_canvas.find_withtag(item_id):
            app.map_canvas.delete(item_id)
    except tk.TclError: pass

