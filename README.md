(Begin Response)
MESSAGE ID: 2 CURRENT FILE: README.md CURRENT PHASE: 2.3.7 (General parameter tuning) CURRENT TASK: Provide the updated README.md content as a downloadable file.
Alright, I will generate the updated README.md file for you to download.

Python

import display

# Updated README.md content based on previous confirmation
readme_content = """# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics, eventually aiming for detailed item provenance tracking and emergent market dynamics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations, eventually featuring more detailed settlements and specialized AI agents. This Python prototype serves as a testbed for core mechanics before a potential future migration to a different engine (e.g., Unity DOTS).

## Current Status (April 2025 - End of Phase 2.6 Implementation)

* **Configuration (`config.json`):**
    * Core simulation parameters externalized (pricing, consumption, trade limits/logic, population thresholds, upkeep, migration, building costs/effects, min trade qty, log lengths, upgrade triggers, transport cost, max trade cost %, dynamic needs factors/thresholds, production wealth buffer, **food abandonment threshold/ticks**, etc.).
    * UI display parameters externalized (shipment marker radius/offset, animation frame delay, etc.).
    * Goods definitions externalized (incl. color, good_type).
    * Building definitions section added (Market Level 2 defined).
* **Recipes (`recipes.json`):** Externalized production recipes. Updated Bread/Wood recipes.
* **Core Logic (`trade_logic.py`):**
    * Settlements with population, terrain, wealth, dynamic storage, labor pools, 3D coordinates. Tracks **ticks below food/wealth thresholds**, **total trades completed**.
    * Market level tracked per settlement, calculating dynamic trade capacity.
    * Basic AI implemented for settlements to upgrade markets based on trade failures. Basic upgrade progress implemented.
    * Goods loaded from config (incl. color, good_type), supporting bulk/item tracking (currently abstract).
    * Recipe-based production. Production logic allows `FOOD` type goods below wealth buffer.
    * Population-driven consumption. **Consumption needs are now dynamic**. **Bread prioritized** over Grain for all settlements.
    * Dynamic local price calculation (incorporates dynamic needs).
    * Bulk trade execution based on price differentials, affordability, storage space, per-settlement trade capacity, transport costs, and max trade cost wealth percentage. Uses configurable `min_trade_qty`. **Increments trade counters.**
    * Trade duration implemented (in-transit goods) with precise timing (departure/arrival seconds).
    * Storage upkeep costs.
    * **Refined settlement abandonment logic:** Triggers on low wealth OR prolonged food shortage. **Migrates population fully** upon abandonment; settlement object/goods persist initially.
    * Population migration logic based on wealth and 3D distance, with per-tick tracking.
    * **Global good total calculation includes in-transit goods.**
    * **Global average price calculation method added.**
    * **Global trade volume per good tracked.**
    * Improved commenting and code structure. Uses configurable log lengths.
* **World Setup (`world_setup.py`):**
    * Dynamically creates goods from config (incl. color, good_type).
    * Sets up initial settlements with standardized population and wealth. Passes sim params and building defs.
    * Passes tick duration to World object.
    * Improved commenting and code structure.
* **User Interface (Refactored into Modules):**
    * Main application logic in `ui_main.py`. **Column weights adjusted.** **Animation pauses when simulation paused.**
    * UI components organized into `ui_static_pane.py`, `ui_dynamic_pane.py`, `ui_map_pane.py`, `ui_analysis_window.py`.
    * Fullscreen Tkinter UI with dark mode (`sv_ttk` optional). Optimized performance.
    * **Static Pane:** Displays Settlements list (updates pop., indicates abandoned), Goods list, Recipe details, Global Goods Totals, **Global Average Prices**, **Global Trade Volume**. Fixed NameError crash.
    * **Settlement Details Tab:** Scrollable area with individual sections per settlement (showing basic stats, Inventory, Production This Tick, Market Level, Trade Capacity, **Total Trades**, **Internal State (Needs>1.0, Food/Wealth Ticks)**). Optimized updates & layout.
    * **Map Tab:** Visualizes settlement locations (2D), name, ID, wealth (scaled size), city status (color). Displays last trade details. Visualizes in-transit shipments as color-coded, offset markers with smooth animation decoupled from tick rate. Includes goods legend.
    * **Trade Analysis Window:** Pop-up window with tabs for Executed, Failed, Potential trades, and Migration events. **Displays Price/Unit clearly.** **Default size reduced.** Optimized updates.
    * Simulation starts correctly in a paused state. Separate loops for simulation ticks and smooth animation.

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
    * **2.2 (Trade Logistics & Visualization):** - *Completed.*
    * **2.3 (Economic Balancing I):**
        * **2.3.1-2.3.6:** Economic Logic & Abandonment Refinements - *Completed.*
    * **2.4 (Tick Timing Fix):** - *Completed.*
    * **2.6 (Enhanced Data Display & Analysis UI):** - *Completed.*
    * **2.3.7 (NEXT):** General parameter tuning.

* **Phase 3: Storage, Wealth & Analysis**
    * **3.1:** Evaluate Storage Limits -> Implement **Storehouse Buildings** (configurable, adds to `storage_capacity`, requires build cost/time). Define initial building types in `config.json` (or separate `buildings.json`).
    * **3.2:** Implement **Detailed Data Export** feature (CSV/JSON dump of settlement state, global state, trade logs per tick or on demand).
    * **3.3:** Implement **Headless Mode** (CLI execution, run for N ticks, output summary/file).
    * **3.4:** Economic Balancing II (Adjust parameters based on Storehouse impact and longer runs).
    * **3.5:** Handle **Negative Wealth** more gracefully (e.g., production stops completely, migration chance increases drastically, potential for debt mechanics later).
    * **3.6:** Implement "Low Wealth" alerts/tracking in UI similar to low food.

* **Phase 4: UI/UX Overhaul**
    * **4.1:** Implement **Improved Map Visuals** (Consider options beyond basic Tkinter Canvas - e.g., visual cues for terrain, resource icons, better representation of Z-coordinate if feasible).
    * **4.2:** Refactor **Recipe display** to pop-out window/separate tab instead of static pane.
    * **4.3:** Implement **Map-Linked Side Panel** for Settlement Details (clicking settlement on map shows details in a dedicated panel, perhaps replacing legend temporarily).
    * **4.4:** Implement **Good Distribution** view (triggered by selecting a good in static pane, highlights settlements holding it on map, maybe shows percentages).
    * **4.5:** Relocate static pane tables (Settlements, Goods, Globals, Averages, Volume) to a dedicated "Global Stats" tab or incorporate into map side panel (from 4.3).
    * **4.6:** General UI cleanup and improvements (layout consistency, tooltips, etc.).

* **Phase 5: Item Provenance & Emergent Markets**
    * **5.1:** Implement **Detailed Item Tracking**:
        * Introduce `ItemInstance` class in `trade_logic.py` for non-bulk goods.
        * Differentiate between bulk (quantity tracked) and tracked goods (list of `ItemInstance`).
        * Add `OriginSettlementID`, `TradeHistory` to `ItemInstance`.
        * Modify `produce`, `consume`, `add/remove_from_storage`, `execute_trades` to handle `ItemInstance`.
        * *Performance consideration: Limit tracking to valuable/crafted goods initially.*
    * **5.2:** Implement **Item Component Tracking** (Add `components` list to `ItemInstance` for crafted goods, linking back to input items/bulk resources).
    * **5.3:** Introduce **Emergent Markets**:
        * Add `MarketLevel` attribute to `Settlement`.
        * Implement logic for `MarketLevel` increase (based on trade volume, wealth, population).
        * Define `MarketLevel` effects in `config.json` (e.g., slight price volatility reduction, attract more abstract trade/future agents, potential minor trade capacity boost independent of building upgrades).
        * Add `MarketLevel` display to UI (Settlement Details).
    * **5.4:** Implement **UI for Item Tracking** (Ability to inspect `ItemInstance` details - origin, history, components - potentially via drill-down in Settlement Details pane).

* **Phase 6: Towards Agent-Based Simulation (Conceptual)**
    * **6.1:** Initial **Agent & Building** Structures:
        * Define basic `Agent` and `Building` classes in `trade_logic.py`.
        * Refactor `Settlement` to act as a container/manager for `Agent` and `Building` objects.
        * Replace `Settlement.population` integer with a list/dict of simple `Agent` objects (initially, maybe just type and basic needs).
        * Define initial `Agent` and `Building` types in configuration (`agents.json`?, `buildings.json`?).
    * **6.2:** **Delegate Core Logic**:
        * Begin shifting `produce` logic to specific `Agent` types working at `Building` types (e.g., Farmer Agent at Field Building).
        * Begin shifting `consume` logic to `Agent` needs (e.g., Agents require Food).
        * Consider moving price calculation to a central `Market` building within the settlement.
    * **6.3:** **Agent Needs & State**: Introduce more complex agent state (inventory, current task) and universal needs (e.g., food, shelter).
    * **6.4:** **Market Information / Broadcasting Needs**: Explore mechanisms for settlements/markets to broadcast needs/surpluses, potentially influencing abstract trade or future agent decisions.
    * **6.5:** **Internal Settlement Coordinates**: Consider if internal buildings/agents need relative coordinates within a settlement's area for future detailed visualization/interaction.
    * **6.6:** **World Simulation Step Expansion**: Add phases for Agent actions (task execution) and Building management to `World.simulation_step`.
    * *Note: This phase focuses on setting up the structures; full agent behavior is likely Phase 7+ or the Unity version.*

* **Phase 7+ ("V2.0" / Long Term - Python Prototype):**
    * Expand Agent behaviors (pathfinding between buildings, complex task selection).
    * Implement Trader Agents making decisions based on `ItemInstance` details and market broadcasts.
    * Introduce more building types and interactions.
    * Consider basic loan/debt mechanics between settlements or agents.
    * Refine simulation balance based on outcomes from agent interactions.
    * Define clear **API/Interfaces** for potential interaction with external world/civilization layers.
    * Address simulation artifacts (e.g., seed oversupply - implement goods decay?).
    * Consider making Wealth a physical good ('Money') that needs transport.

## Long-Term Vision (Post-Prototype / Unity Engine)

This Python prototype serves as a foundation for exploring core simulation mechanics. The eventual goal is to rebuild and expand upon these concepts within the **Unity Engine**, leveraging the **Data-Oriented Technology Stack (DOTS)** for performance and scalability. Key aspects of this future vision include:

* **Data-Driven Core:** Maintain the principle of the world state being defined by data, managed efficiently by Unity's Entity Component System (ECS). Configuration files (`Building`, `Agent`, `Recipe` definitions) will drive entity setup.
* **3D Spherical World:** Simulate on a spherical topology with (x, y, z) coordinates, allowing for realistic latitude-based climate, sun cycles, and potentially underground exploration.
* **Emergent World Generation:** Move away from predefined settlements towards generating geography, climate, biomes, rivers, and resources based on simulating underlying physical processes (e.g., solar insolation, altitude effects, atmospheric/hydrological cycles, basic geology). Settlements arise organically based on resource availability and agent actions.
* **Tile-Based Visualization (Primary):** Render the 3D world data using 2D slices at different Z-levels, similar to Dwarf Fortress, allowing clear visualization of layers and potentially complex underground structures. Data structures will aim for flexibility to potentially support other rendering methods later (e.g., simplified 3D view).
* **Complex Agent Simulation:** Utilize DOTS to simulate large numbers of individual agents (people, creatures) with detailed needs (food, shelter, social, etc.), skills, inventories, schedules, goals, and behaviors, interacting within the emergent world and buildings.
* **Detailed Building Simulation:** Buildings become entities constructed by agents, providing specific functions (housing, workshops, storage, markets), requiring maintenance, and potentially having internal layouts.
* **Physics-Based Logistics:** Transport considers terrain, vehicle types (carts, ships), infrastructure (roads, ports), weight/volume, and agent/resource availability.

## Technologies (Current Prototype)

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration