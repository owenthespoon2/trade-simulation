# Emergent Trade Simulation Prototype

## Project Goal

This project aims to prototype a data-driven simulation where a complex, large-scale trade network emerges between settlements based on local economic factors. Inspired by historical examples like the Silk Road and concepts from complex systems, the simulation models production, consumption, supply, demand, pricing, and logistics.

The initial concept originated from [link to your Obsidian note or brief description if not linkable]. The goal is to create a modular system suitable for potential future integration with broader ecosystem or civilization simulations.

## Current Status (April 2025)

* **Core Logic:** Implemented in Python (`trade_logic.py`), featuring:
    * Settlements with population, terrain, wealth, storage, and labor pools.
    * Goods with base values, bulk/item tracking (`ItemInstance` for provenance).
    * Recipe-based production system loaded from `recipes.json`, requiring inputs (goods/labor), respecting terrain constraints, and producing outputs.
    * Population-driven consumption.
    * Dynamic local price calculation based on supply/demand ratio.
    * Basic trade execution based on price differentials between settlements.
* **Configuration:** Production recipes are externalized in `recipes.json`. World setup (settlements, initial conditions) is handled in `world_setup.py`.
* **User Interface:** A basic Tkinter UI (`trade_ui.py`) provides:
    * A fullscreen view with dark mode (using `sv_ttk` if available).
    * Side-by-side display of static setup data (Settlements, Goods, interactive Recipe lookup) and dynamic simulation state (Settlement wealth, storage, prices, labor).
    * Real-time updates driven by the simulation ticks.
    * A log of recent trade events.

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
5.  Run the UI:
    ```bash
    python trade_ui.py
    ```

## Future Plans

* Implement population growth mechanics.
* Allow storage capacity to increase (e.g., through investment).
* Add more complex trade logic (e.g., transportation costs, trader agents, multi-stop routes).
* Introduce more specific producer/consumer entities (Farms, Mines, Workshops, Households) to replace settlement-level abstractions.
* Refine resource chains and add more goods/recipes.
* Potential integration with geographical map data.

## Technologies

* Python 3
* Tkinter (via `ttk` and `sv_ttk`) for the UI
* JSON for configuration

