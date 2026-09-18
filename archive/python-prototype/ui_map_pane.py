import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import math
import random
import traceback # Added for error printing
from collections import defaultdict # Added for grouping shipments
import time # Added for smooth animation timing

# Import Good class for type hinting/checking if needed later
from trade_logic import Good

def setup_map_pane(parent_frame, app):
    """
    Sets up the widgets for the 'Map' tab (canvas, info labels, legend).
    """
    # --- Map Canvas (Column 0) ---
    map_canvas_frame = ttk.Frame(parent_frame)
    map_canvas_frame.grid(row=0, column=0, rowspan=3, sticky="nsew")
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
    legend_container.grid(row=0, column=1, rowspan=3, sticky="ns", padx=(5,0))
    legend_container.rowconfigure(1, weight=0)
    legend_container.rowconfigure(2, weight=1)

    ttk.Label(legend_container, text="Goods Key", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.NW, pady=(0,5))
    app.goods_legend_frame = ttk.Frame(legend_container)
    app.goods_legend_frame.grid(row=1, column=0, sticky="nsew")

    _update_goods_legend(app)


def update_map_pane_tick_based(app):
    """
    Updates map elements that change based on the simulation tick:
    settlement visuals, last trade label, and manages shipment marker
    creation/deletion.

    Args:
        app (SimulationUI): The main application instance.
    """
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return

    # 1. Update Settlement Visuals (Size/Color)
    _update_settlement_visuals(app)

    # 2. Update "Last Trade Details" Label
    last_trade_details = None
    trades_this_tick = list(app.world.executed_trade_details_this_tick)
    if trades_this_tick:
        last_trade_details = trades_this_tick[-1]
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
                  f"Goods Cost: {goods_cost:.2f}, TCost: {transport_cost:.2f}, ETA: T{eta_tick})")
        if hasattr(app, 'last_trade_info_var'): app.last_trade_info_var.set(info)
        if hasattr(app, 'last_trade_reason_var'): app.last_trade_reason_var.set(reason)

    # 3. Manage Shipment Markers (Create/Delete/Store Offset)
    _manage_shipment_markers(app)

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
        _create_single_settlement_item(app, settlement)
    _update_settlement_visuals(app)

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
             _create_single_settlement_item(app, settlement)

def _create_single_settlement_item(app, settlement):
    """Creates canvas items for a single new settlement."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    if settlement.id in app.settlement_canvas_items: return
    x, y, _ = app.settlement_coords[settlement.id]; r = app.SETTLEMENT_BASE_RADIUS
    color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR
    circle_id = app.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=app.DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}"))
    text_id = app.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=app.DARK_FG, font=app.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}"))
    wealth_id = app.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=app.WEALTH_TEXT_COLOR, font=app.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}"))
    app.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}

# --- Helper for Offset Calculation ---
def _calculate_offset(x1, y1, x2, y2, index, total_overlapping, offset_distance):
    """Calculates the perpendicular offset for a marker."""
    offset_x = 0.0
    offset_y = 0.0
    if total_overlapping > 1:
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)

        if length > 1e-6: # Avoid division by zero
            # Normalized direction vector
            nx = dx / length
            ny = dy / length
            # Perpendicular vector
            px = -ny
            py = nx
            # Calculate offset magnitude based on index and total overlapping
            offset_magnitude = (index - (total_overlapping - 1) / 2.0) * offset_distance
            offset_x = px * offset_magnitude
            offset_y = py * offset_magnitude
    return offset_x, offset_y

# --- Shipment Marker Management (Tick-Based) ---
def _manage_shipment_markers(app):
    """
    Creates new shipment markers, deletes completed ones, and stores
    their offset vectors. Called once per simulation tick.
    """
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return

    current_shipment_ids_in_sim = {s['shipment_id'] for s in app.world.in_transit_shipments}
    existing_marker_ids = set(app.shipment_markers.keys())

    # --- Group current shipments by route ---
    shipments_by_route = defaultdict(list)
    for shipment in app.world.in_transit_shipments:
        route_key = (shipment['seller_id'], shipment['buyer_id'])
        shipments_by_route[route_key].append(shipment)

    # --- Create or update markers ---
    for route_key, shipments_on_route in shipments_by_route.items():
        num_overlapping = len(shipments_on_route)

        for shipment_index, shipment in enumerate(shipments_on_route):
            shipment_id = shipment['shipment_id']

            # Get coordinates
            seller_coords = app.settlement_coords.get(shipment['seller_id'])
            buyer_coords = app.settlement_coords.get(shipment['buyer_id'])
            if not seller_coords or not buyer_coords: continue # Skip if coords missing

            x1, y1, _ = seller_coords
            x2, y2, _ = buyer_coords

            # Calculate the offset for this shipment
            offset_x, offset_y = _calculate_offset(
                x1, y1, x2, y2,
                shipment_index, num_overlapping,
                app.SHIPMENT_MARKER_OFFSET
            )

            # If marker doesn't exist, create it
            if shipment_id not in app.shipment_markers:
                # Calculate initial position based on tick progress (approximate)
                world_tick = app.world.tick
                departure_tick = shipment['departure_tick']
                arrival_tick = shipment['arrival_tick']
                total_duration_ticks = max(1, arrival_tick - departure_tick)
                ticks_elapsed = max(0, world_tick - departure_tick) # Ensure non-negative
                progress = min(1.0, ticks_elapsed / total_duration_ticks) # Clamp progress

                initial_x = x1 + (x2 - x1) * progress + offset_x
                initial_y = y1 + (y2 - y1) * progress + offset_y
                marker_r = app.SHIPMENT_MARKER_RADIUS
                good_id = shipment['good_id']
                marker_color = app.good_colors.get(good_id, app.DEFAULT_SHIPMENT_COLOR)

                try:
                    marker_item_id = app.map_canvas.create_oval(
                        initial_x - marker_r, initial_y - marker_r,
                        initial_x + marker_r, initial_y + marker_r,
                        fill=marker_color,
                        outline="",
                        tags=("shipment_marker", shipment_id)
                    )
                    # Store marker ID and its calculated offset vector
                    app.shipment_markers[shipment_id] = {
                        'item_id': marker_item_id,
                        'offset_x': offset_x,
                        'offset_y': offset_y
                    }
                except tk.TclError as e:
                    print(f"WARN: TclError creating shipment marker {shipment_id}: {e}")
            else:
                 # If marker exists, ensure its offset is updated (in case route density changed)
                 # This might cause a slight visual jump if many shipments start/end on the same tick
                 if shipment_id in app.shipment_markers:
                     app.shipment_markers[shipment_id]['offset_x'] = offset_x
                     app.shipment_markers[shipment_id]['offset_y'] = offset_y


    # --- Remove markers for completed/cancelled shipments ---
    ids_to_remove = existing_marker_ids - current_shipment_ids_in_sim
    for shipment_id in ids_to_remove:
        if shipment_id in app.shipment_markers: # Check existence before deleting
            marker_data = app.shipment_markers[shipment_id]
            _delete_canvas_item(app, marker_data['item_id'])
            del app.shipment_markers[shipment_id]


# --- Smooth Shipment Animation (Called by Animation Loop) ---
def update_shipment_marker_positions_smoothly(app):
    """
    Updates the visual position of existing shipment markers based on
    real-time progress. Called frequently by the animation loop.
    """
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    if not hasattr(app, 'world') or not hasattr(app.world, 'in_transit_shipments'): return

    current_time = time.perf_counter()
    shipments_dict = {s['shipment_id']: s for s in app.world.in_transit_shipments}

    # Use items() for potentially safer iteration if dict changes, though less likely here
    for shipment_id, marker_data in list(app.shipment_markers.items()):
        shipment = shipments_dict.get(shipment_id)
        marker_item_id = marker_data['item_id']

        # Check if the corresponding shipment still exists and item is on canvas
        if not shipment or not app.map_canvas.find_withtag(marker_item_id):
            # If shipment disappeared or marker was deleted, remove from tracking
            if shipment_id in app.shipment_markers:
                _delete_canvas_item(app, marker_item_id) # Attempt deletion just in case
                del app.shipment_markers[shipment_id]
            continue

        try:
            # Get coordinates and timing
            seller_coords = app.settlement_coords.get(shipment['seller_id'])
            buyer_coords = app.settlement_coords.get(shipment['buyer_id'])

            # Check if coordinates are valid
            if not seller_coords or not buyer_coords:
                 # Silently skip update if settlement coords missing, marker will be removed next tick
                 continue

            x1, y1, _ = seller_coords
            x2, y2, _ = buyer_coords
            departure_time = shipment['departure_time_sec']
            arrival_time = shipment['arrival_time_sec']

            # Calculate progress based on time
            total_duration = arrival_time - departure_time
            elapsed_time = current_time - departure_time

            # Ensure total_duration is positive to avoid division by zero or negative progress
            if total_duration <= 1e-6:
                progress = 1.0 # Consider it arrived if duration is negligible
            else:
                progress = max(0.0, min(1.0, elapsed_time / total_duration)) # Clamp progress

            # Interpolate base position
            base_x = x1 + (x2 - x1) * progress
            base_y = y1 + (y2 - y1) * progress

            # Retrieve stored offset
            offset_x = marker_data['offset_x']
            offset_y = marker_data['offset_y']

            # Final position
            final_x = base_x + offset_x
            final_y = base_y + offset_y
            marker_r = app.SHIPMENT_MARKER_RADIUS

            # Update marker position
            app.map_canvas.coords(marker_item_id,
                                  final_x - marker_r, final_y - marker_r,
                                  final_x + marker_r, final_y + marker_r)

        except tk.TclError:
            # Handle cases where the marker might disappear between checks
            print(f"WARN: TclError updating position for shipment marker {shipment_id}. Removing tracker.")
            if shipment_id in app.shipment_markers:
                del app.shipment_markers[shipment_id] # Remove broken marker tracker
        except KeyError as e:
             print(f"WARN: Missing key {e} in shipment data for {shipment_id} during smooth update.")
             # Optionally remove the marker if data is corrupt
             # if shipment_id in app.shipment_markers:
             #     _delete_canvas_item(app, marker_item_id)
             #     del app.shipment_markers[shipment_id]
        except Exception as e:
             print(f"ERROR during smooth update for shipment {shipment_id}: {e}")
             traceback.print_exc()


# --- Legend Update ---
def _update_goods_legend(app):
    """Populates the goods legend frame with color squares and names."""
    if not hasattr(app, 'goods_legend_frame') or not app.goods_legend_frame.winfo_exists():
        print("WARN: Legend frame not ready for update.")
        return

    for widget in app.goods_legend_frame.winfo_children(): widget.destroy()

    row_index = 0
    if not hasattr(app, 'world') or not app.world.goods:
        print("WARN: World or goods not ready for legend update.")
        return
    # Safer sort using get with a default Good object
    sorted_good_ids = sorted(app.good_colors.keys(), key=lambda gid: app.world.goods.get(gid, Good(gid, "?", 0)).name)

    for good_id in sorted_good_ids:
        color = app.good_colors.get(good_id, app.DEFAULT_SHIPMENT_COLOR)
        good_name = app.world.goods.get(good_id, Good(good_id, f"Unknown ({good_id})", 0)).name

        color_box = tk.Frame(app.goods_legend_frame, width=10, height=10, bg=color, relief=tk.SOLID, borderwidth=1)
        color_box.grid(row=row_index, column=0, padx=(0, 3), pady=1)
        label = ttk.Label(app.goods_legend_frame, text=good_name, font=app.legend_font)
        label.grid(row=row_index, column=1, sticky=tk.W)
        row_index += 1

# --- Canvas Item Helpers ---
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
