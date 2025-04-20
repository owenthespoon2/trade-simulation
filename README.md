# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations.

## Current Status (April 2025)

* **Configuration:**
    * Core simulation parameters (price sensitivity, consumption rates, trade limits, population thresholds, upkeep costs, etc.) externalized to `config.json`.
    * UI display parameters (tick delays, colors, sizes) externalized to `config.json`.
    * Goods definitions (name, base value, properties) externalized to `config.json`.
    * Production recipes remain externalized in `recipes.json`.
    * World setup (initial settlement placement, terrain, population, initial wealth/stock) configured in `world_setup.py`.
* **Core Logic:** Implemented in Python (`trade_logic.py`), featuring:
    * Settlements with population, terrain, wealth, dynamic storage capacity (larger for cities), and labor pools.
    * Goods loaded from config, supporting bulk/item tracking (`ItemInstance` for non-bulk provenance).
    * Recipe-based production system loaded from `recipes.json`.
    * Population-driven consumption, with larger "cities" (above population threshold) requiring "bread" produced from "grain".
    * Dynamic local price calculation based on supply/demand ratio (configurable sensitivity, min/max).
    * Trade execution based on price differentials (configurable profit margin threshold).
    * Storage upkeep costs deducted from wealth each tick to discourage hoarding.
* **World Setup:**
    * `world_setup.py` dynamically creates goods from config.
    * Generates a configurable number of smaller settlements with randomized placement (improved spacing) alongside predefined major settlements.
* **User Interface:** A Tkinter UI (`trade_ui.py`) provides:
    * A fullscreen view with dark mode (using `sv_ttk` if available).
    * **Tabbed Interface:** Separates detailed tables from the map visualization.
    * **Tables Tab:** Displays static setup data (Settlements list, Goods list, interactive Recipe lookup) and dynamic simulation state (Settlement wealth, storage, prices, labor) in sortable tables, plus a log of recent trade events.
    * **Map Tab:**
        * Visualizes settlement locations (`tk.Canvas`).
        * Displays settlement name, ID, and current wealth.
        * Scales settlement circle size based on wealth (logarithmic scaling, configurable).
        * Colors settlements differently if they meet the "city" population threshold.
        * Shows recent trade routes with flashing lines and marker dots indicating direction.
        * Displays details of the last trade (participants, good, quantity, prices, profit) below the map.
    * Real-time updates driven by configurable simulation ticks (`tick_delay_ms`).

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

## Known Issues / Future Plans

* **Economic Balancing:** The simulation can still stagnate or lead to wealth depletion, especially with storage costs. Further tuning of production costs, consumption rates, upkeep costs, and potentially adding wealth generation mechanisms (e.g., taxes, trade tariffs, resource extraction value) is needed.
* **Negative Wealth:** Need to implement logic for what happens when a settlement's wealth drops significantly below zero (e.g., production stops, population decline, abandonment).
* **Settlement Placement:** While improved, the random placement might still result in some suboptimal spacing or clustering.
* Implement population growth/decline mechanics.
* Add more complex trade logic (e.g., transportation costs, dedicated trader agents, multi-stop routes).
* Introduce more specific producer/consumer entities (Farms, Mines, Workshops, Households).
* Refine resource chains and add more intermediate/luxury goods.
* Potential integration with geographical map data.

## Technologies

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration
