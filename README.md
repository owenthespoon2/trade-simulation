# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents. This Python prototype serves as a testbed for core mechanics before a potential future migration to a different engine (e.g., Unity DOTS).

## Current Status (April 2025 - End of Phase 2.3.2 Implementation)

* **Configuration (`config.json`):**
    * Core simulation parameters externalized (pricing, consumption, trade limits/logic, population thresholds, upkeep, migration, building costs/effects, min trade qty, log lengths, upgrade triggers, transport cost, max trade cost %, **dynamic needs factors/thresholds**, **production wealth buffer**, etc.).
    * UI display parameters externalized (**shipment marker radius/offset**, **animation frame delay**, etc.).
    * Goods definitions externalized (incl. **color**, **good\_type**).
    * Building definitions section added (Market Level 2 defined).
* **Recipes (`recipes.json`):** Externalized production recipes.
* **Core Logic (`trade_logic.py`):**
    * Settlements with population, terrain, wealth, dynamic storage, labor pools, 3D coordinates.
    * Market level tracked per settlement, calculating dynamic trade capacity.
    * Basic AI implemented for settlements to upgrade markets based on trade failures. Basic upgrade progress implemented.
    * Goods loaded from config (incl. **color**, **good\_type**), supporting bulk/item tracking.
    * Recipe-based production. **Production logic allows `FOOD` type goods below wealth buffer.**
    * Population-driven consumption. **Consumption needs are now dynamic**, adjusting based on fulfillment ratio.
    * Dynamic local price calculation (incorporates dynamic needs).
    * Bulk trade execution based on price differentials, affordability, storage space, per-settlement trade capacity, transport costs, and max trade cost wealth percentage. Uses configurable `min_trade_qty`.
    * **Trade duration implemented** (in-transit goods) with **precise timing** (departure/arrival seconds).
    * Storage upkeep costs.
    * Settlement abandonment logic.
    * Population migration logic based on wealth and 3D distance, with per-tick tracking.
    * Global good total calculation method.
    * Improved commenting and code structure. Uses configurable log lengths.
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config (incl. **color**, **good\_type**).
    * Sets up initial settlements with standardized population and wealth. Passes sim params and building defs.
    * Passes **tick duration** to World object.
    * Improved commenting and code structure.
* **User Interface (Refactored into Modules):**
    * Main application logic in `ui_main.py`.
    * UI components organized into `ui_static_pane.py`, `ui_dynamic_pane.py`, `ui_map_pane.py`, `ui_analysis_window.py`.
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional). Optimized performance.
    * **Static Pane:** Displays Settlements list (updates pop.), Goods list, Recipe details, Global Goods Totals.
    * **Settlement Details Tab:** Scrollable area with individual sections per settlement (showing basic stats, Inventory, Production This Tick, Market Level, Trade Capacity). Optimized updates & layout.
    * **Map Tab:** Visualizes settlement locations (2D), name, ID, wealth (scaled size), city status (color). Displays last trade details. **Visualizes in-transit shipments** as color-coded, offset markers with **smooth animation** decoupled from tick rate. Includes goods legend.
    * **Trade Analysis Window:** Pop-up window with tabs for Executed, Failed, Potential trades, and Migration events. Displays Transport Cost details. Optimized updates.
    * Simulation starts correctly in a paused state. **Separate loops for simulation ticks and smooth animation.**

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
    * **2.2 (Trade Logistics & Visualization):**
        * Implement Transport Costs - *Completed.*
        * Add UI display for Transport Costs - *Completed.*
        * Correct KeyError in map pane display - *Completed.*
        * Correct trade viability check logic - *Completed.*
        * Implement Max Trade Cost Wealth Percentage limit - *Completed.*
        * Implement Trade Duration (in-transit goods) - *Completed.*
        * **2.2c:** Visualize in-transit trades (Color-coding, Offsetting) - *Completed.*
        * Implement **Smooth Shipment Animation** - *Completed.*
    * **2.3 (Economic Balancing I):**
        * **2.3.1:** Review/Refine Price Calculation Mechanism (Dynamic Needs) - *Completed.*
        * **2.3.2:** Refine `production_wealth_buffer` Logic (Using `good_type`) - *Completed.*
        * **2.3.3 (NEXT):** Address seed oversupply (Goods Decay?).
        * **2.3.4:** Modify **Bread recipe** to require **Wood**.
        * **2.3.5:** Modify **Wood recipe** to require **Tools**.
        * **2.3.6:** Review/Fix **Tool** production/display issue.
        * **2.3.7:** Implement **Abandonment due to Lack of Food**.
        * **2.3.8:** General parameter tuning.
    * **2.4 (Tick Timing Fix):** - *Completed.*
    * **2.5 (UI Enhancements):** (To be done after 2.3.8)
        * **2.5.1:** Add "Needs" visualization to Settlement Details tab (`ui_dynamic_pane.py`).
        * **2.5.2:** Adjust main column weights for better layout (`ui_main.py`).

* **Phase 3: Storage, Wealth & Analysis**
    * **3.1:** Evaluate Storage Limits -> Implement **Storehouse Buildings** (if needed).
    * **3.2:** Implement **Detailed Data Export** feature.
    * **3.3:** Economic Balancing II.
    * **3.4:** Handle **Negative Wealth** more gracefully.

* **Phase 4: UI/UX Overhaul**
    * **4.1:** Implement **Improved Map Visuals**.
    * **4.2:** Refactor **Recipe display** to pop-out window/separate tab instead of static pane.
    * **4.3:** Implement **Map-Linked Side Panel** for Settlement Details (replaces legend area on selection).
    * **4.4:** General UI cleanup and improvements.

* **Phase 5: Towards Agent-Based Simulation**
    * **5.1:** Population Dynamics.
    * **5.2:** Introduce simple specialized **Agent types**.
    * **5.3:** Consider **Universal Needs**.
    * **5.4:** Explore **Market Information / Broadcasting Needs** mechanisms (Allow settlements to signal high needs, potentially differentiated by `good_type`, influencing trader decisions).

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
