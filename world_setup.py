import json
import sys
from collections import defaultdict, OrderedDict
import random

# ==============================================================================
# FILE INDEX
# ==============================================================================
# - Imports                               : Line 5
# - setup_world Function                  : Line 16
#   - Load Configuration                  : Line 20 (Loads sim_params, goods_defs, building_defs)
#   - Initialize World                    : Line 51 (Passes sim_params, building_defs)
#   - Define Goods (from Config)          : Line 55
#   - Load Recipes                        : Line 76
#   - Define Settlements                  : Line 96 (Passes sim_params, building_defs to constructor)
#   - Add Initial Stock                   : Line 153
#   - Define Regions & Civilizations      : Line 169
# - Test Block (`if __name__ == "__main__"`) : Line 186
# ==============================================================================


# --- Import Core Logic Classes ---
try:
    # Ensure we import the updated Settlement class definition from trade_logic
    from trade_logic import World, Good, Settlement, Region, Civilization, ItemInstance
except ImportError as e:
    # Provide a helpful error message if the core logic file is missing
    print("-" * 50); print("FATAL ERROR: Cannot import classes from 'trade_logic.py'."); print(f"ImportError: {e}"); print("Please ensure 'trade_logic.py' exists, is in the same directory, and is runnable."); print("-" * 50); sys.exit(1)

# --- Simulation Setup Function ---
def setup_world(config_file="config.json", recipe_file="recipes.json"):
    """
    Creates and initializes the simulation world state.

    Loads simulation parameters, goods definitions, building definitions, and recipes
    from JSON files, creates initial settlements, regions, and civilizations,
    and adds initial stock to settlements.

    Args:
        config_file (str): Path to the main configuration JSON file.
        recipe_file (str): Path to the recipes JSON file.

    Returns:
        World: The fully initialized World object.

    Raises:
        SystemExit: If configuration files are missing critical data or cannot be parsed.
    """

    # --- Load Configuration ---
    print(f"Attempting to load configuration from: {config_file}")
    sim_params = {}
    goods_defs = {}
    building_defs = {} # NEW: Load building definitions
    try:
        with open(config_file, 'r') as f: config_data = json.load(f)
        sim_params = config_data.get("simulation_parameters", {})
        goods_defs = config_data.get("goods_definitions", {})
        building_defs = config_data.get("building_definitions", {}) # NEW: Load building definitions
        print(f"Successfully loaded configuration from {config_file}")
    except FileNotFoundError:
        print(f"ERROR: Config file '{config_file}' not found. Using default parameters.")
        # Define default sim_params if file not found (consider if this is desired behavior)
        sim_params = { "price_sensitivity": 2.0, "storage_capacity_per_pop": 10.0, "max_trades_per_tick": 200, "labor_per_pop": 0.5, "trade_profit_margin_threshold": 1.05, "settlement_default_initial_wealth": 500, "base_consumption_rate": 0.1, "max_production_passes": 5, "min_price_multiplier": 0.1, "max_price_multiplier": 10.0, "city_population_threshold": 150, "city_storage_multiplier": 1.5, "storage_cost_per_unit": 0.01, "production_wealth_buffer": 10.0, "abandonment_wealth_threshold": -100, "abandonment_ticks_threshold": 15, "migration_check_interval": 5, "migration_wealth_threshold": 0, "migration_target_min_wealth": 600, "migration_max_percentage": 0.1, "base_trade_capacity": 5, "market_upgrade_fail_trigger": 5, "min_trade_qty": 0.01, "settlement_log_max_length": 10, "world_trade_log_max_length": 10 }
        goods_defs = {} # No default goods
        building_defs = {} # No default buildings
    except json.JSONDecodeError: print(f"ERROR: Could not decode JSON from '{config_file}'. Check file format. Exiting."); sys.exit(1)
    except Exception as e: print(f"ERROR: An unexpected error occurred loading config: {e}. Exiting."); sys.exit(1)

    if not goods_defs: print("ERROR: No goods definitions found in config file or defaults. Cannot setup world."); sys.exit(1)
    if not sim_params: print("ERROR: No simulation parameters found in config file or defaults. Cannot setup world."); sys.exit(1)
    # It's okay if building_defs is empty initially

    # --- Initialize World with Simulation Parameters and Building Definitions ---
    print("Initializing World object...")
    # NEW: Pass sim_params and building_defs to World constructor
    world = World(sim_params=sim_params, building_defs=building_defs)

    # --- Define Goods Dynamically from Config ---
    print("Loading goods definitions...")
    for good_id, definition in goods_defs.items():
        try:
            good = Good(id=good_id, name=definition['name'], base_value=float(definition['base_value']), is_bulk=bool(definition.get('is_bulk', True)), is_producible=bool(definition.get('is_producible', False)))
            world.add_good(good)
        except KeyError as ke: print(f"ERROR: Missing required key {ke} in goods definition for '{good_id}'. Skipping.")
        except Exception as e: print(f"ERROR: Could not create good '{good_id}' from definition: {e}. Skipping.")

    if not world.goods: print("ERROR: No valid goods were loaded. Cannot continue."); sys.exit(1)
    print(f"Loaded {len(world.goods)} goods.")

    # --- Load Recipes ---
    print(f"Attempting to load recipes from: {recipe_file}")
    try:
        with open(recipe_file, 'r') as f: recipes_data = json.load(f)
        print(f"Successfully loaded recipes from {recipe_file}")
        for good_id, recipe_info in recipes_data.items():
            if good_id in world.goods:
                good = world.goods[good_id]
                if good.is_producible:
                    try: good.add_recipe(**recipe_info)
                    except Exception as e: print(f"ERROR: Failed to add recipe for '{good_id}': {e}")
    except FileNotFoundError: print(f"WARN: Recipe file '{recipe_file}' not found. No recipes loaded.")
    except json.JSONDecodeError: print(f"ERROR: Could not decode JSON from '{recipe_file}'. Check format.")
    except Exception as e: print(f"ERROR: An unexpected error occurred loading recipes: {e}")

    # --- Define Settlements ---
    print("Defining initial settlements...")
    # Get parameters needed for Settlement initialization from sim_params
    default_wealth = sim_params.get('settlement_default_initial_wealth', 500)

    # Standardized starting population and wealth for testing
    standard_start_pop = 100
    standard_start_wealth = default_wealth # Use the default value from config
    print(f"NOTE: Standardizing starting population to {standard_start_pop} and wealth to {standard_start_wealth} for all settlements.")

    settlements_to_add = []
    # FUTURE: This section will need significant changes to define initial internal buildings and agent populations.
    # NEW: Pass sim_params and building_defs to the Settlement constructor
    settlements_to_add.append(Settlement(
        id='A', name='Farmstead', region_id='R1', population=standard_start_pop, terrain_type='Grassland',
        sim_params=sim_params, building_defs=building_defs, # Pass params and defs
        initial_wealth=standard_start_wealth, # Use standard wealth
        x=100, y=100, z=0
    ))
    settlements_to_add.append(Settlement(
        id='B', name='Logger\'s Camp', region_id='R1', population=standard_start_pop, terrain_type='Forest',
        sim_params=sim_params, building_defs=building_defs, # Pass params and defs
        initial_wealth=standard_start_wealth, # Use standard wealth
        x=100, y=300, z=5
    ))
    settlements_to_add.append(Settlement(
        id='C', name='Mine Town', region_id='R2', population=standard_start_pop, terrain_type='Mountain',
        sim_params=sim_params, building_defs=building_defs, # Pass params and defs
        initial_wealth=standard_start_wealth, # Use standard wealth
        x=400, y=100, z=20
    ))
    settlements_to_add.append(Settlement(
        id='D', name='Craftburg', region_id='R2', population=standard_start_pop, terrain_type='Hills',
        sim_params=sim_params, building_defs=building_defs, # Pass params and defs
        initial_wealth=standard_start_wealth, # Use standard wealth
        x=400, y=300, z=10
    ))
    settlements_to_add.append(Settlement(
        id='E', name='Metropolis', region_id='R2', population=standard_start_pop, terrain_type='Plains',
        sim_params=sim_params, building_defs=building_defs, # Pass params and defs
        initial_wealth=standard_start_wealth, # Use standard wealth
        x=250, y=200, z=0
    ))

    # Add Settlements to World
    for s in settlements_to_add: world.add_settlement(s)

    # --- Add Initial Stock ---
    print("Adding initial stock to settlements...")
    try:
        if 'seed' in world.goods: world.settlements['A'].add_to_storage(world.goods['seed'], quantity=5, tick=-1)
        if 'grain' in world.goods: world.settlements['A'].add_to_storage(world.goods['grain'], quantity=50, tick=-1)
        if 'wood' in world.goods: world.settlements['B'].add_to_storage(world.goods['wood'], quantity=30, tick=-1)
        if 'iron_ore' in world.goods: world.settlements['C'].add_to_storage(world.goods['iron_ore'], quantity=10, tick=-1)
        if 'wood' in world.goods: world.settlements['D'].add_to_storage(world.goods['wood'], quantity=10, tick=-1)
        if 'iron_ore' in world.goods: world.settlements['D'].add_to_storage(world.goods['iron_ore'], quantity=5, tick=-1)
        if 'grain' in world.goods: world.settlements['E'].add_to_storage(world.goods['grain'], quantity=100, tick=-1)
    except KeyError as ke:
        print(f"ERROR: Could not add initial stock. Settlement or Good ID '{ke}' not found.")
        print("       Check settlement IDs in world_setup.py and good IDs in config.json.")
    except Exception as e: print(f"ERROR: Failed to add initial stock: {e}")

    # --- Define Regions & Civilizations ---
    print("Defining regions and civilizations...")
    region1 = Region('R1', 'Green Valley'); region2 = Region('R2', 'Grey Peaks')
    for s in world.settlements.values():
        if s.region_id == 'R1': region1.add_settlement(s)
        elif s.region_id == 'R2': region2.add_settlement(s)
    world.add_region(region1); world.add_region(region2)
    civ1 = Civilization('C1', 'The Settlers')
    civ1.add_region(region1); civ1.add_region(region2)
    world.add_civilization(civ1)

    print(f"World setup complete with {len(world.settlements)} settlements.")
    return world

# --- Optional: Test setup ---
if __name__ == "__main__":
    print("="*30); print("Executing world_setup.py directly for testing..."); print("="*30)
    try:
        test_world = setup_world()
        print("-" * 20); print("Goods defined:")
        for good in test_world.goods.values(): print(f"  - {good} (Producible: {good.is_producible}, Recipe: {'Yes' if good.recipe else 'No'})")
        print("-" * 20); print("Settlements created:")
        for settlement in test_world.get_all_settlements(): print(f"  - {settlement} (Storage Cap: {settlement.storage_capacity:.0f}, Labor Pool: {settlement.max_labor_pool:.1f}, Market Lvl: {settlement.market_level}, Trade Cap: {settlement.trade_capacity})") # Added market info
        print("-" * 20); print("Regions created:")
        for region in test_world.regions.values(): print(f"  - {region.name} (Settlements: {[s.name for s in region.settlements]})")
        print("-" * 20); print("Setup test complete."); print("="*30)
    except Exception as e:
        print(f"\n--- ERROR DURING WORLD SETUP TEST ---"); print(e)
        import traceback; traceback.print_exc(); print("-" * 35)
