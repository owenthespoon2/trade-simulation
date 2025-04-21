# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents.

## Current Status (April 2025 - Post Phase 1.8.6)

* **Configuration:**
    * Core simulation parameters externalized to `config.json`.
    * UI display parameters externalized to `config.json`.
    * Goods definitions externalized to `config.json` (Textiles removed).
    * Production recipes remain externalized in `recipes.json`.
* **Core Logic (`trade_logic.py`):**
    * Settlements with population, terrain, wealth, dynamic storage, labor pools, 3D coordinates.
    * Goods loaded from config, supporting bulk/item tracking.
    * Recipe-based production with wealth buffer check and per-tick production tracking (`production_this_tick`).
    * Population-driven consumption.
    * Dynamic local price calculation.
    * **Bulk trade execution** based on price differentials, affordability, and storage space.
    * Storage upkeep costs.
    * Settlement abandonment logic.
    * Population migration logic based on wealth and 3D distance, with per-tick tracking.
    * Global good total calculation method (`get_global_good_totals`).
    * Improved commenting and code structure.
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config.
    * Sets up initial settlements with specified parameters (incl. Z coordinates).
    * Improved commenting and code structure.
* **User Interface (Refactored into Modules):**
    * Main application logic in `ui_main.py`.
    * UI components organized into `ui_static_pane.py`, `ui_dynamic_pane.py`, `ui_map_pane.py`, `ui_analysis_window.py`.
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional).
    * **Static Pane:** Displays Settlements list (updates pop.), Goods list, Recipe details, **Global Goods Totals**.
    * **Settlement Details Tab:** Redesigned with a **scrollable area** containing individual sections per settlement. Each section shows basic stats, **Inventory** (Treeview), and **Production This Tick** (Treeview). Uses an **optimized update strategy** (persisting widgets) to prevent lag/flashing. Minor layout shift fixed.
    * **Map Tab:** Visualizes settlement locations (2D projection), name, ID, wealth (scaled size), city status (color). Shows recent trade routes. Displays last trade details.
    * **Trade Analysis Window:** Pop-up window with tabs for Executed, Failed, Potential trades, and Migration events. Update logic **optimized** to only run when the window is visible.
    * Simulation now starts correctly in a **paused state**.

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

We are following a phased development approach:

* **Phase 0 - 1.8.6:** Initial setup, core logic implementation, UI creation, bulk trades, UI enhancements (3D coords, migration/production/global stats), refactoring, and performance optimizations - *Completed.*

* **Phase 2: Core Economic Tuning & Trade Realism** (Focus: Make the current simulation more robust and believable)
    * **2.1:** Evaluate Trade Volume -> Implement **Market Buildings** (Dynamic trade capacity per settlement) *if observation indicates this is a bottleneck*.
    * **2.2:** Implement **Transport Costs** based on distance/trade value. (Medium Complexity)
    * **2.3:** Economic Balancing I (Review pricing floors/ceilings, production costs vs. sale prices, address specific issues like the seed oversupply. Consider simple **Goods Decay** for food items). (Medium Complexity)

* **Phase 3: Storage, Wealth & Analysis**
    * **3.1:** Evaluate Storage Limits -> Implement **Storehouse Buildings** (Dynamic storage capacity) *if observation indicates this is a bottleneck*.
    * **3.2:** Implement **Detailed Data Export** feature (Button to save settlement history to JSON). (Medium Complexity, High RAM potential)
    * **3.3:** Economic Balancing II (Refine based on previous changes).
    * **3.4:** Handle **Negative Wealth** more gracefully (e.g., halt production/trade, faster abandonment). (Medium Complexity)

* **Phase 4: UI/UX Overhaul**
    * **4.1:** Implement **Improved Map Visuals** (Top-down view, better settlement representation [e.g., squares], region/civ display, click-info, alternative trade visualization [e.g., moving dots]). (High Complexity UI work)
    * *(UI Code Refactoring into modules completed in Phase 1.8.5)*

* **Phase 5: Towards Agent-Based Simulation** (Focus: Starting the shift from settlement-level to agent-level)
    * **5.1:** Population Dynamics (Implement simple growth/decline mechanics). (Medium Complexity)
    * **5.2:** Introduce simple specialized **Agent types** (e.g., basic workers vs. traders affecting efficiency). (Medium-High Complexity)
    * **5.3:** Consider **Universal Needs** (e.g., Universal Bread Consumption) and impact on balance. (Medium Complexity - High Rebalancing Effort)

* **Phase 6+ ("V2.0" / Long Term):**
    * Full **Entity System** (Model individual Farms, Workshops, Houses within settlements). (Very High Complexity)
    * Full **Agent-Based Model** (Agents with needs, inventories, tasks, schedules, AI decision-making). (Very High Complexity)
    * **Wealth as Coin** (Physical currency simulation). (High Complexity Refactor)
    * **Loans/Banks** system. (High Complexity)
    * **Long-Term Deals** / Contracts. (Medium-High Complexity)
    * Advanced Resource Chains, Luxury Goods, etc.

## Technologies

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration
