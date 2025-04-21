import tkinter as tk
from tkinter import ttk
import tkinter.font as tkFont
import math
import random
import traceback # Added for error printing

def setup_map_pane(parent_frame, app):
    """
    Sets up the widgets for the 'Map' tab (canvas, info labels).

    Args:
        parent_frame (ttk.Frame): The parent frame for this pane (the tab).
        app (SimulationUI): The main application instance.
    """
    ttk.Label(parent_frame, text="Trade Map", font=("Arial", 12, "bold")).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
    # Store map canvas reference on app instance
    app.map_canvas = tk.Canvas(parent_frame, bg=app.CANVAS_BG, width=500, height=400, highlightthickness=0) # Use app.CANVAS_BG
    app.map_canvas.grid(row=1, column=0, sticky="nsew")

    # Fonts are already stored on app instance

    # Info Frame (Below Map)
    info_frame = ttk.LabelFrame(parent_frame, text="Last Trade Details (This Tick)", padding="5")
    info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
    info_frame.columnconfigure(0, weight=1)
    # Use Tkinter variables stored on app instance
    last_trade_label = ttk.Label(info_frame, textvariable=app.last_trade_info_var, wraplength=450)
    last_trade_label.grid(row=0, column=0, sticky=tk.W)
    last_trade_reason_label = ttk.Label(info_frame, textvariable=app.last_trade_reason_var)
    last_trade_reason_label.grid(row=1, column=0, sticky=tk.W)


def update_map_pane(app):
    """
    Updates the map visualization (settlement visuals, trade routes) each tick.

    Args:
        app (SimulationUI): The main application instance.
    """
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return

    _update_settlement_visuals(app) # Update settlement visuals

    # Draw trade routes and update info labels
    last_trade_details = None
    trades_this_tick = list(app.world.executed_trade_details_this_tick)
    if trades_this_tick:
        for trade_info in trades_this_tick:
            _draw_trade_route(app, trade_info)
            last_trade_details = trade_info
    else:
        if hasattr(app, 'last_trade_info_var'): app.last_trade_info_var.set("No trades this tick.")
        if hasattr(app, 'last_trade_reason_var'): app.last_trade_reason_var.set("")

    if last_trade_details:
        info = (f"Trade: {last_trade_details['quantity']:.1f} {last_trade_details['good_name']} " f"from {last_trade_details['seller_name']} to {last_trade_details['buyer_name']}")
        reason = (f"Reason: Sell P={last_trade_details['seller_price']:.2f}, " f"Buy P={last_trade_details['buyer_price']:.2f} " f"(Profit/U={last_trade_details['profit_per_unit']:.2f})")
        if hasattr(app, 'last_trade_info_var'): app.last_trade_info_var.set(info)
        if hasattr(app, 'last_trade_reason_var'): app.last_trade_reason_var.set(reason)


# --- Visualization Drawing Methods ---

def _calculate_settlement_radius(app, wealth):
    """Calculates settlement radius based on wealth."""
    try: radius_increase = math.sqrt(max(0, wealth)) * app.SETTLEMENT_WEALTH_SCALE_PARAM # Use app.CONSTANT
    except ValueError: radius_increase = 0
    capped_increase = min(radius_increase, app.SETTLEMENT_MAX_RADIUS_INCREASE) # Use app.CONSTANT
    return app.SETTLEMENT_BASE_RADIUS + capped_increase # Use app.CONSTANT

def create_settlement_canvas_items(app):
    """Creates the initial visual representation of settlements."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    app.map_canvas.delete("settlement"); app.settlement_canvas_items.clear()
    for settlement in app.settlements:
        x, y, _ = app.settlement_coords[settlement.id]
        r = app.SETTLEMENT_BASE_RADIUS # Use app.CONSTANT
        color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR # Use app.CONSTANTs
        circle_id = app.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=app.DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}")) # Use app.DARK_FG
        text_id = app.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=app.DARK_FG, font=app.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}")) # Use app.DARK_FG
        wealth_id = app.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=app.WEALTH_TEXT_COLOR, font=app.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}")) # Use app.WEALTH_TEXT_COLOR
        app.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
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
                current_color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR # Use app.CONSTANTs
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
    x, y, _ = app.settlement_coords[settlement.id]; r = app.SETTLEMENT_BASE_RADIUS # Use app.CONSTANT
    color = app.CITY_COLOR if settlement.population >= app.CITY_POP_THRESHOLD else app.SETTLEMENT_COLOR # Use app.CONSTANTs
    circle_id = app.map_canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline=app.DARK_FG, width=1, tags=("settlement", f"settlement_{settlement.id}")) # Use app.DARK_FG
    text_id = app.map_canvas.create_text(x, y + r + 8, text=f"{settlement.name} ({settlement.id})", fill=app.DARK_FG, font=app.settlement_font, anchor=tk.CENTER, tags=("settlement", f"settlement_{settlement.id}")) # Use app.DARK_FG
    wealth_id = app.map_canvas.create_text(x, y - r - 8, text=f"W: {settlement.wealth:.0f}", fill=app.WEALTH_TEXT_COLOR, font=app.wealth_font, anchor=tk.CENTER, tags=("settlement", "wealth_text", f"settlement_{settlement.id}")) # Use app.WEALTH_TEXT_COLOR
    app.settlement_canvas_items[settlement.id] = {'circle': circle_id, 'text': text_id, 'wealth': wealth_id}
    _update_settlement_visuals(app)

def _draw_trade_route(app, trade_info):
    """Draws a temporary line and marker on the map."""
    if not hasattr(app, 'map_canvas') or not app.map_canvas.winfo_exists(): return
    seller_id = trade_info['seller_id']; buyer_id = trade_info['buyer_id']
    if seller_id not in app.settlement_coords or buyer_id not in app.settlement_coords: return
    x1, y1, _ = app.settlement_coords[seller_id]; x2, y2, _ = app.settlement_coords[buyer_id]
    trade_tag = f"trade_{seller_id}_{buyer_id}_{app.world.tick}_{random.randint(1000,9999)}"

    # Access constants via app instance
    TRADE_ROUTE_FLASH_COLOR = app.TRADE_ROUTE_FLASH_COLOR
    TRADE_ROUTE_COLOR = app.TRADE_ROUTE_COLOR
    TRADE_MARKER_COLOR = app.TRADE_MARKER_COLOR
    TRADE_EFFECT_DURATION_MS = app.TRADE_EFFECT_DURATION_MS
    TRADE_MARKER_RADIUS = app.TRADE_MARKER_RADIUS

    line_id = app.map_canvas.create_line(x1, y1, x2, y2, fill=TRADE_ROUTE_FLASH_COLOR, width=2.5, arrow=tk.LAST, tags=("trade_route", trade_tag))
    app.root.after(300, lambda lid=line_id: _set_item_color(app, lid, TRADE_ROUTE_COLOR))
    app.root.after(TRADE_EFFECT_DURATION_MS, lambda lid=line_id: _delete_canvas_item(app, lid))

    marker_r = TRADE_MARKER_RADIUS; dx = x1 - x2; dy = y1 - y2; dist = max(1, (dx**2 + dy**2)**0.5)
    buyer_settlement = app.world.settlements.get(buyer_id); current_buyer_radius = app.SETTLEMENT_BASE_RADIUS
    if buyer_settlement: current_buyer_radius = _calculate_settlement_radius(app, buyer_settlement.wealth)
    offset_scale = current_buyer_radius + marker_r + 2; marker_x = x2 + (dx / dist) * offset_scale; marker_y = y2 + (dy / dist) * offset_scale
    marker_id = app.map_canvas.create_oval(marker_x - marker_r, marker_y - marker_r, marker_x + marker_r, marker_y + marker_r, fill=TRADE_MARKER_COLOR, outline="", tags=("trade_marker", trade_tag))
    app.root.after(TRADE_EFFECT_DURATION_MS, lambda mid=marker_id: _delete_canvas_item(app, mid))

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

