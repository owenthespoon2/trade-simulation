# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents.

## Current Status (April 2025 - Post Phase 2.1 Logic)

* **Configuration (`config.json`):**
    * Core simulation parameters externalized (pricing, consumption, trade limits/logic, population thresholds, upkeep, migration, building costs/effects, **min trade qty, log lengths, upgrade triggers**, etc.).
    * UI display parameters externalized.
    * Goods definitions externalized (Textiles removed).
    * **Building definitions** section added (Market Level 2 defined with costs).
* **Recipes (`recipes.json`):** Externalized production recipes.
* **Core Logic (`trade_logic.py`):**
    * Settlements with population, terrain, wealth, dynamic storage, labor pools, 3D coordinates.
    * **Market level** tracked per settlement, calculating dynamic **trade capacity**.
    * Basic AI implemented for settlements to **upgrade markets** based on trade failures (using config trigger). Basic upgrade progress implemented.
    * Goods loaded from config, supporting bulk/item tracking.
    * Recipe-based production with wealth buffer check and per-tick production tracking.
    * Population-driven consumption.
    * Dynamic local price calculation.
    * **Bulk trade execution** based on price differentials, affordability, storage space, and **per-settlement trade capacity**. Uses configurable `min_trade_qty`.
    * Storage upkeep costs.
    * Settlement abandonment logic.
    * Population migration logic based on wealth and 3D distance, with per-tick tracking.
    * Global good total calculation method.
    * Improved commenting and code structure. Uses configurable log lengths.
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config.
    * Sets up initial settlements with **standardized population and wealth**. Passes sim params and building defs.
    * Improved commenting and code structure.
* **User Interface (Refactored into Modules):**
    * Main application logic in `ui_main.py`.
    * UI components organized into `ui_static_pane.py`, `ui_dynamic_pane.py`, `ui_map_pane.py`, `ui_analysis_window.py`.
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional). Optimized performance.
    * **Static Pane:** Displays Settlements list (updates pop.), Goods list, Recipe details, Global Goods Totals.
    * **Settlement Details Tab:** Scrollable area with individual sections per settlement (showing basic stats, Inventory, Production This Tick). Optimized updates & layout.
    * **Map Tab:** Visualizes settlement locations (2D), name, ID, wealth (scaled size), city status (color). Shows recent trade routes. Displays last trade details.
    * **Trade Analysis Window:** Pop-up window with tabs for Executed, Failed, Potential trades, and Migration events. Optimized updates.
    * Simulation starts correctly in a paused state.

## Running the Simulation

1.  Ensure Python 3 is installed.
2.  Clone the repository / ensure all `.py`, `.json` files are present.
3.  (Optional but recommended) Create and activate a virtual environment.
4.  Install dependencies: `pip install sv_ttk`
5.  Modify `config.json` / `recipes.json` as needed.
6.  Run the main UI script:
    ```bash
    python ui_main.py
    ```

## Development Plan & Future Goals

* **Phase 0 - 2.1 (Logic):** Initial setup, core logic implementation, UI creation, bulk trades, UI enhancements, refactoring, performance optimizations, Market building logic & config parameters - *Completed.*

* **Phase 2: Core Economic Tuning, Trade Realism & Infrastructure**
    * **2.1 (UI - NEXT):** Add UI display for Market Level and Trade Capacity in settlement details (`ui_dynamic_pane.py`).
    * **2.2:** Implement **Transport Costs** based on distance.
    * **2.3:** Economic Balancing I:
        * Review/Refine **Price Calculation Mechanism**.
        * Review `production_wealth_buffer` logic.
        * Address seed oversupply (Goods Decay?).
        * Modify **Bread recipe** to require **Wood**.
        * Modify **Wood recipe** to require **Tools**.
        * Review/Fix **Tool** production/display issue.
        * Implement **Abandonment due to Lack of Food**.
        * General parameter tuning (incl. Market costs/effects).
    * **2.4:** Investigate/Address **Tick Timing Irregularity**.

* **Phase 3: Storage, Wealth & Analysis**
    * **3.1:** Evaluate Storage Limits -> Implement **Storehouse Buildings** (if needed).
    * **3.2:** Implement **Detailed Data Export** feature.
    * **3.3:** Economic Balancing II.
    * **3.4:** Handle **Negative Wealth** more gracefully.

* **Phase 4: UI/UX Overhaul**
    * **4.1:** Implement **Improved Map Visuals**.

* **Phase 5: Towards Agent-Based Simulation**
    * **5.1:** Population Dynamics.
    * **5.2:** Introduce simple specialized **Agent types**.
    * **5.3:** Consider **Universal Needs**.

* **Phase 6+ ("V2.0" / Long Term):**
    * Full **Entity System**.
    * Full **Agent-Based Model**.
    * **Wealth as Coin**.
    * **Loans/Banks**.
    * **Long-Term Deals**.

## Technologies

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration
