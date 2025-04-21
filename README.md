# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents.

## Current Status (April 2025 - Post Phase 0.5)

* **Configuration:**
    * Core simulation parameters (price sensitivity, consumption rates, trade limits, population thresholds, upkeep costs, migration rules, etc.) externalized to `config.json`.
    * UI display parameters (tick delays, colors, sizes) externalized to `config.json`.
    * Goods definitions (name, base value, properties) externalized to `config.json`.
    * Production recipes remain externalized in `recipes.json`.
* **Core Logic (`trade_logic.py`):**
    * Settlements represented with population, terrain, wealth, dynamic storage capacity (larger for cities), labor pools, and now **3D coordinates (x, y, z)**.
    * Goods loaded from config, supporting bulk/item tracking (`ItemInstance` for non-bulk provenance).
    * Recipe-based production system loaded from `recipes.json`, including basic wealth buffer check to halt production when funds are low.
    * Population-driven consumption, with city-specific needs (e.g., bread).
    * Dynamic local price calculation based on supply/demand ratio.
    * Trade execution based on price differentials (currently limited trade quantity per transaction).
    * Storage upkeep costs deducted from wealth each tick.
    * Settlement abandonment logic based on sustained low wealth.
    * **Population migration** logic based on wealth differentials and 3D distance.
    * Improved commenting and code structure (file index added).
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config.
    * Sets up initial settlements with specified parameters, including initial wealth, stock, and **Z coordinates**.
    * Improved commenting and code structure (file index added).
* **User Interface (`trade_ui.py`):**
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional).
    * Tabbed Interface: Separates detailed tables from the map visualization.
    * **Tables Tab:** Displays static setup data (Settlements, Goods, Recipes) and dynamic simulation state (Settlement wealth, storage, prices, labor) in sortable tables, plus a log of recent trade events.
    * **Map Tab:** Visualizes settlement locations (2D projection of X,Y), name, ID, and wealth. Scales settlement circle size based on wealth. Colors settlements differently if they meet the "city" population threshold. Shows recent trade routes with flashing lines/markers. Displays details of the last trade.
    * **Trade Analysis Window:** Provides detailed views of:
        * Executed Trades (this tick)
        * Failed Trade Executions (this tick)
        * Viable Potential Trades (this tick)
        * **Migration Events (this tick)** - New!
    * Improved commenting and code structure (file index added).

## Running the Simulation

1.  Ensure Python 3 is installed.
2.  Clone the repository.
3.  (Optional but recommended) Create and activate a virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate  # Windows
    ```
4.  Install dependencies:
    ```bash
    pip install sv_ttk
    ```
5.  Ensure `config.json` and `recipes.json` are present in the same directory as the Python scripts. Modify these files to tune parameters, goods, or recipes.
6.  Run the UI:
    ```bash
    python trade_ui.py
    ```

## Development Plan & Future Goals

We are following a phased development approach:

* **Phase 0:** Confirm existing mechanics (Abandonment, Migration, Production Halt) - *Completed.*
* **Phase 0.5:** Implement 3D Coordinates & Migration Tracking UI - *Completed.*
* **Phase 1 (Next):** Implement Bulk Trading Logic & Add Code Comments.
* **Phase 2:** Evaluate Trade Volume & Potentially Implement Market Buildings.
* **Phase 3:** Evaluate Storage Limits & Potentially Implement Storehouse Buildings.

**Longer-Term Vision / Future Plans:**

* **Economic Balancing:** Continue tuning parameters (production costs, consumption, upkeep, trade logic) to achieve more stable and interesting economic behaviour. Address potential stagnation or runaway wealth/poverty.
* **Agent-Based Model:** Transition from settlement-level logic to individual agents (Traders, Miners, Farmers, etc.) with specific roles, inventories, needs, and behaviours operating within settlements.
* **Detailed Settlement Composition:** Model settlements as collections of functional buildings (Houses, Workshops, Mines, Markets, Town Halls) instead of monolithic entities. Agents would interact with these buildings.
* **Advanced Trade Logic:** Implement features like transportation costs (based on distance/terrain), dedicated trader agents, multi-stop routes, and potentially trade agreements.
* **Population Dynamics:** Add mechanics for population growth/decline based on factors like food availability, wealth, housing.
* **Enhanced Map Visualization:** Move beyond the basic canvas to a more sophisticated map rendering system, potentially capable of showing terrain, settlement details, and agent movements.
* **Resource Chain Refinement:** Add more intermediate and complex goods (e.g., metal -> tools, grain -> flour -> bread).

## Technologies

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration
