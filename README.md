# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents. This Python prototype serves as a testbed for core mechanics before a potential future migration to a different engine (e.g., Unity DOTS).

## Current Status (April 2025 - End of Phase 2.2 Implementation)

* **Configuration (`config.json`):**
    * Core simulation parameters externalized (pricing, consumption, trade limits/logic, population thresholds, upkeep, migration, building costs/effects, min trade qty, log lengths, upgrade triggers, **transport cost**, **max trade cost %**, etc.).
    * UI display parameters externalized.
    * Goods definitions externalized.
    * Building definitions section added (Market Level 2 defined).
* **Recipes (`recipes.json`):** Externalized production recipes.
* **Core Logic (`trade_logic.py`):**
    * Settlements with population, terrain, wealth, dynamic storage, labor pools, 3D coordinates.
    * Market level tracked per settlement, calculating dynamic trade capacity.
    * Basic AI implemented for settlements to upgrade markets based on trade failures. Basic upgrade progress implemented.
    * Goods loaded from config, supporting bulk/item tracking.
    * Recipe-based production with wealth buffer check and per-tick tracking.
    * Population-driven consumption.
    * Dynamic local price calculation.
    * Bulk trade execution based on price differentials, affordability, storage space, per-settlement trade capacity, **transport costs**, and **max trade cost wealth percentage**. Uses configurable `min_trade_qty`.
    * Storage upkeep costs.
    * Settlement abandonment logic.
    * Population migration logic based on wealth and 3D distance, with per-tick tracking.
    * Global good total calculation method.
    * Improved commenting and code structure. Uses configurable log lengths.
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config.
    * Sets up initial settlements with standardized population and wealth. Passes sim params and building defs.
    * Improved commenting and code structure.
* **User Interface (Refactored into Modules):**
    * Main application logic in `ui_main.py`.
    * UI components organized into `ui_static_pane.py`, `ui_dynamic_pane.py`, `ui_map_pane.py`, `ui_analysis_window.py`.
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional). Optimized performance.
    * **Static Pane:** Displays Settlements list (updates pop.), Goods list, Recipe details, Global Goods Totals.
    * **Settlement Details Tab:** Scrollable area with individual sections per settlement (showing basic stats, Inventory, Production This Tick, **Market Level**, **Trade Capacity**). Optimized updates & layout.
    * **Map Tab:** Visualizes settlement locations (2D), name, ID, wealth (scaled size), city status (color). Shows recent trade routes. Displays last trade details (incl. **Transport Cost**).
    * **Trade Analysis Window:** Pop-up window with tabs for Executed, Failed, Potential trades, and Migration events. Displays **Transport Cost** details. Optimized updates.
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

## Development Plan & Future Goals (Python Prototype)

* **Phase 0 - 2.1 (Logic & UI):** Initial setup, core logic implementation, UI creation, bulk trades, UI enhancements, refactoring, performance optimizations, Market building logic & config parameters, Market UI display - *Completed.*

* **Phase 2: Core Economic Tuning, Trade Realism & Infrastructure**
    * **2.2 (Logic):** Implement **Transport Costs** based on distance (`config.json`, `trade_logic.py`) - *Completed.*
    * **2.2 (UI):** Add UI display for Transport Costs in Trade Analysis window (`ui_analysis_window.py`) - *Completed.*
    * **2.2 (UI Fix):** Correct KeyError in map pane display (`ui_map_pane.py`) - *Completed.*
    * **2.2 (Logic Fix):** Correct trade viability check logic in `trade_logic.py` - *Completed.*
    * **2.2 (Logic):** Implement **Max Trade Cost Wealth Percentage** limit (`config.json`, `trade_logic.py`) - *Completed.*
    * **2.2b (Logic - NEXT):** Implement basic **Trade Duration** (in-transit goods).
    * **2.2c (UI - Future):** Visualize in-transit trades on Map (e.g., moving markers).
    * **2.2d (Logic - Future):** Implement multiple transport types/speeds.
    * **2.3 (Economic Balancing I):**
        * Review/Refine **Price Calculation Mechanism** (address min/max hitting).
        * Review `production_wealth_buffer` logic.
        * Address seed oversupply (Goods Decay?).
        * Modify **Bread recipe** to require **Wood**.
        * Modify **Wood recipe** to require **Tools**.
        * Review/Fix **Tool** production/display issue.
        * Implement **Abandonment due to Lack of Food**.
        * General parameter tuning (incl. Market costs/effects, Transport Costs, Price Sensitivity, Wealth Percentage).
    * **2.4:** Investigate/Address **Tick Timing Irregularity** (ensure consistent delay between ticks, explore performance options within Tkinter/Python).

* **Phase 3: Storage, Wealth & Analysis**
    * **3.1:** Evaluate Storage Limits -> Implement **Storehouse Buildings** (if needed).
    * **3.2:** Implement **Detailed Data Export** feature.
    * **3.3:** Economic Balancing II.
    * **3.4:** Handle **Negative Wealth** more gracefully.

* **Phase 4: UI/UX Overhaul**
    * **4.1:** Implement **Improved Map Visuals**.
    * **4.2:** Refactor **Recipe display** to pop-out window/separate tab instead of static pane.
    * **4.3:** General UI cleanup and improvements.

* **Phase 5: Towards Agent-Based Simulation**
    * **5.1:** Population Dynamics.
    * **5.2:** Introduce simple specialized **Agent types**.
    * **5.3:** Consider **Universal Needs**.

* **Phase 6+ ("V2.0" / Long Term - Python Prototype):**
    * Explore more complex agent interactions.
    * Consider basic loan/debt mechanics.
    * Refine simulation based on balancing outcomes.

## Long-Term Vision (Post-Prototype / Unity Engine)

This Python prototype serves as a foundation for exploring core simulation mechanics. The eventual goal is to rebuild and expand upon these concepts within the **Unity Engine**, leveraging the **Data-Oriented Technology Stack (DOTS)** for performance and scalability. Key aspects of this future vision include:

* **Data-Driven Core:** Maintain the principle of the world state being defined by data, managed efficiently by Unity's Entity Component System (ECS).
* **3D Spherical World:** Simulate on a spherical topology with (x, y, z) coordinates, allowing for realistic latitude-based climate, sun cycles, and potentially underground exploration.
* **Emergent World Generation:** Move away from predefined settlements towards generating geography, climate, biomes, rivers, and resources based on simulating underlying physical processes (e.g., solar insolation, altitude effects, atmospheric/hydrological cycles, basic geology).
* **Tile-Based Visualization (Primary):** Render the 3D world data using 2D slices at different Z-levels, similar to Dwarf Fortress, allowing clear visualization of layers and potentially complex underground structures. Data structures will aim for flexibility to potentially support other rendering methods later.
* **Complex Agent Simulation:** Utilize DOTS to simulate large numbers of individual agents (people, creatures) with more detailed needs, behaviors, and interactions within the emergent world.

## Technologies (Current Prototype)

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration
