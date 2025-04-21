import tkinter as tk
from tkinter import ttk
import traceback # Added for error printing

# Optional theme import - handled in ui_main now

def open_analysis_window(app):
    """
    Opens or focuses the trade & migration analysis window.

    Args:
        app (SimulationUI): The main application instance.
    """
    if app.analysis_window and app.analysis_window.winfo_exists():
        app.analysis_window.lift(); return

    app.analysis_window = tk.Toplevel(app.root)
    app.analysis_window.title(f"Trade & Migration Analysis (Tick {app.world.tick})")
    app.analysis_window.geometry("1000x700")

    try: # Basic theme background setting
        if app.SV_TTK_AVAILABLE: app.analysis_window.configure(bg=app.DARK_BG)
    except Exception as e: print(f"WARN: Could not apply theme bg to analysis window: {e}")

    app.analysis_window.rowconfigure(0, weight=1); app.analysis_window.columnconfigure(0, weight=1)
    notebook = ttk.Notebook(app.analysis_window); notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

    # Define Tabs and Columns
    exec_frame = ttk.Frame(notebook, padding=5); notebook.add(exec_frame, text="Executed Trades")
    exec_frame.rowconfigure(0, weight=1); exec_frame.columnconfigure(0, weight=1)
    exec_cols = ('From', 'To', 'Good', 'Qty', 'Sell P', 'Buy P', 'Profit/U', 'Total Val')
    app.analysis_tree_executed = _create_analysis_treeview(exec_frame, exec_cols, app)

    fail_frame = ttk.Frame(notebook, padding=5); notebook.add(fail_frame, text="Failed Executions")
    fail_frame.rowconfigure(0, weight=1); fail_frame.columnconfigure(0, weight=1)
    fail_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Reason')
    app.analysis_tree_failed = _create_analysis_treeview(fail_frame, fail_cols, app)

    pot_frame = ttk.Frame(notebook, padding=5); notebook.add(pot_frame, text="Viable Potential Trades")
    pot_frame.rowconfigure(0, weight=1); pot_frame.columnconfigure(0, weight=1)
    pot_cols = ('From', 'To', 'Good', 'Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q')
    app.analysis_tree_potential = _create_analysis_treeview(pot_frame, pot_cols, app)

    mig_frame = ttk.Frame(notebook, padding=5); notebook.add(mig_frame, text="Migration")
    mig_frame.rowconfigure(0, weight=1); mig_frame.columnconfigure(0, weight=1)
    mig_cols = ('Tick', 'From', 'To', 'Quantity')
    app.analysis_tree_migration = _create_analysis_treeview(mig_frame, mig_cols, app)

    update_analysis_window(app) # Populate with current data
    app.analysis_window.protocol("WM_DELETE_WINDOW", lambda: _on_analysis_window_close(app))


def update_analysis_window(app):
    """
    Updates the data displayed in the trade analysis window, ONLY if it exists.

    Args:
        app (SimulationUI): The main application instance.
    """
    # <<< OPTIMIZATION: Only update if the window exists and is valid >>>
    if not app.analysis_window or not app.analysis_window.winfo_exists():
        return # Do nothing if the window isn't open

    # Update window title (safe even if called when window exists)
    app.analysis_window.title(f"Trade & Migration Analysis (Tick {app.world.tick})")

    # --- Update Executed Trades Tab ---
    # Check each treeview exists before updating
    if hasattr(app, 'analysis_tree_executed') and app.analysis_tree_executed and app.analysis_tree_executed.winfo_exists():
        app.analysis_tree_executed.delete(*app.analysis_tree_executed.get_children())
        for trade in app.world.executed_trade_details_this_tick:
            values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['quantity']:.1f}", f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", f"{trade['quantity'] * trade['seller_price']:.1f}")
            try: app.analysis_tree_executed.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting executed trade: {e}")

    # --- Update Failed Trades Tab ---
    if hasattr(app, 'analysis_tree_failed') and app.analysis_tree_failed and app.analysis_tree_failed.winfo_exists():
        app.analysis_tree_failed.delete(*app.analysis_tree_failed.get_children())
        sorted_failed = sorted(app.world.failed_trades_this_tick, key=lambda x: x.get('profit_per_unit', 0), reverse=True)
        for trade in sorted_failed:
             qty_avail_str = f"{trade.get('qty_avail', '?'):.1f}" if isinstance(trade.get('qty_avail'), (int,float)) else '?'
             pot_qty_str = f"{trade.get('potential_qty', '?'):.1f}" if isinstance(trade.get('potential_qty'), (int,float)) else '?'
             values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", qty_avail_str, pot_qty_str, trade.get('fail_reason', 'Unknown'))
             try: app.analysis_tree_failed.insert("", tk.END, values=values)
             except Exception as e: print(f"Error inserting failed trade: {e}")

    # --- Update Potential Trades Tab ---
    if hasattr(app, 'analysis_tree_potential') and app.analysis_tree_potential and app.analysis_tree_potential.winfo_exists():
        app.analysis_tree_potential.delete(*app.analysis_tree_potential.get_children())
        viable_potential = [t for t in app.world.potential_trades_this_tick if t.get('is_viable_prelim', False)]
        sorted_potential = sorted(viable_potential, key=lambda x: x['profit_per_unit'], reverse=True)
        for trade in sorted_potential:
            values = (trade['seller_name'], trade['buyer_name'], trade['good_name'], f"{trade['seller_price']:.2f}", f"{trade['buyer_price']:.2f}", f"{trade['profit_per_unit']:.2f}", f"{trade['qty_avail']:.1f}", f"{trade['potential_qty']:.1f}")
            try: app.analysis_tree_potential.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting potential trade: {e}")

    # --- Update Migration Tab ---
    if hasattr(app, 'analysis_tree_migration') and app.analysis_tree_migration and app.analysis_tree_migration.winfo_exists():
        app.analysis_tree_migration.delete(*app.analysis_tree_migration.get_children())
        for migration in app.world.migration_details_this_tick:
            values = (migration['tick'], migration['from_name'], migration['to_name'], migration['quantity'])
            try: app.analysis_tree_migration.insert("", tk.END, values=values)
            except Exception as e: print(f"Error inserting migration event: {e}")


def _create_analysis_treeview(parent, columns, app):
    """Helper function to create a Treeview with scrollbars."""
    frame = ttk.Frame(parent); frame.grid(row=0, column=0, sticky="nsew")
    frame.rowconfigure(0, weight=1); frame.columnconfigure(0, weight=1)
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    tree.grid(row=0, column=0, sticky="nsew")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview); vsb.grid(row=0, column=1, sticky="ns")
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview); hsb.grid(row=1, column=0, sticky="ew")
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    for col in columns:
        anchor = tk.W; width = 90
        if col in ('Sell P', 'Buy P', 'Profit/U', 'Avail Q', 'Pot Q', 'Qty', 'Price', 'Total Val', 'Quantity', 'Tick'): anchor = tk.E; width=70
        if col == 'Reason': width = 250; anchor=tk.W
        if col == 'Good': width = 80
        if col == 'From' or col == 'To': width = 100
        tree.heading(col, text=col, command=lambda c=col: _sort_treeview_column(tree, c, False, app))
        tree.column(col, width=width, anchor=anchor, stretch=tk.NO)
    return tree

def _sort_treeview_column(tv, col, reverse, app):
    """Sorts a Treeview column."""
    # Check if treeview exists before proceeding
    if not tv.winfo_exists(): return
    try:
        l = [];
        for k in tv.get_children(''):
            val = tv.set(k, col)
            try: l.append((float(val), k))
            except ValueError: l.append((str(val).lower(), k)) # Case-insensitive string sort
        l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l): tv.move(k, '', index)
        tv.heading(col, command=lambda c=col: _sort_treeview_column(tv, c, not reverse, app))
    except Exception as e:
        print(f"Error sorting treeview column {col}: {e}")
        # traceback.print_exc() # Optional detailed traceback

def _on_analysis_window_close(app):
    """Callback function when the analysis window is closed."""
    if app.analysis_window:
        app.analysis_window.destroy()
        app.analysis_window = None
        app.analysis_tree_potential = None
        app.analysis_tree_failed = None
        app.analysis_tree_executed = None
        app.analysis_tree_migration = None

