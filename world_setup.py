import json
import sys
from collections import defaultdict, OrderedDict
import random

# ==============================================================================
# FILE INDEX
# ==============================================================================
# - Imports                               : Line 5
# - setup_world Function                  : Line 16
#   - Load Configuration                  : Line 20
#   - Initialize World                    : Line 48
#   - Define Goods (from Config)          : Line 52
#   - Load Recipes                        : Line 73
#   - Define Settlements                  : Line 91
#   - Add Initial Stock                   : Line 137
#   - Define Regions & Civilizations      : Line 153
# - Test Block (`if __name__ == "__main__"`) : Line 170
# ==============================================================================


# --- Import Core Logic Classes ---
try:
    # Ensure we import the updated Settlement class definition from trade_logic
    from trade_logic import World, Good, Settlement, Region, Civilization, ItemInstance
except ImportError as e:
    # Provide a helpful error message if the core logic file is missing
    print("-" * 50)
    print("FATAL ERROR: Cannot import classes from 'trade_logic.py'.")
    print(f"ImportError: {e}")
    print("Please ensure 'trade_logic.py' exists, is in the same directory, and is runnable.")
    print("-" * 50)
    sys.exit(1) # Exit if core logic cannot be imported

# --- Simulation Setup Function ---
def setup_world(config_file="config.json", recipe_file="recipes.json"):
    """
    Creates and initializes the simulation world state.

    Loads simulation parameters, goods definitions, and recipes from JSON files,
    creates initial settlements, regions, and civilizations, and adds initial
    stock to settlements.

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
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        # Get simulation parameters, fallback to empty dict if missing
        sim_params = config_data.get("simulation_parameters", {})
        # Get goods definitions, fallback to empty dict if missing
        goods_defs = config_data.get("goods_definitions", {})
        print(f"Successfully loaded configuration from {config_file}")
    except FileNotFoundError:
        print(f"ERROR: Config file '{config_file}' not found. Using default parameters.")
        # Provide sensible defaults if config is missing - essential for basic operation
        sim_params = {
            "price_sensitivity": 2.0, "storage_capacity_per_pop": 10.0,
            "max_trades_per_tick": 200, "labor_per_pop": 0.5,
            "trade_profit_margin_threshold": 1.05, "settlement_default_initial_wealth": 500,
            "base_consumption_rate": 0.1, "max_production_passes": 5,
            "min_price_multiplier": 0.1, "max_price_multiplier": 10.0,
            "city_population_threshold": 150, "city_storage_multiplier": 1.5,
            "storage_cost_per_unit": 0.01, "production_wealth_buffer": 10.0,
            "abandonment_wealth_threshold": -100, "abandonment_ticks_threshold": 15,
            "migration_check_interval": 5, "migration_wealth_threshold": 0,
            "migration_target_min_wealth": 600, "migration_max_percentage": 0.1
        }
        goods_defs = {} # Cannot proceed without goods definitions
    except json.JSONDecodeError:
        # Handle invalid JSON format
        print(f"ERROR: Could not decode JSON from '{config_file}'. Check file format. Exiting.")
        sys.exit(1)
    except Exception as e:
        # Catch any other unexpected errors during file loading
        print(f"ERROR: An unexpected error occurred loading config: {e}. Exiting.")
        sys.exit(1)

    # Critical check: Ensure goods definitions were loaded
    if not goods_defs:
        print("ERROR: No goods definitions found in config file or defaults. Cannot setup world.")
        sys.exit(1)

    # --- Initialize World with Simulation Parameters ---
    print("Initializing World object...")
    world = World(sim_params)

    # --- Define Goods Dynamically from Config ---
    print("Loading goods definitions...")
    for good_id, definition in goods_defs.items():
        try:
            # Create Good object using data from the definition
            good = Good(
                id=good_id,
                name=definition['name'],
                base_value=float(definition['base_value']),
                # Use .get() for optional keys with defaults
                is_bulk=bool(definition.get('is_bulk', True)),
                is_producible=bool(definition.get('is_producible', False))
            )
            # Add the created Good object to the world's goods dictionary
            world.add_good(good)
        except KeyError as ke:
            # Handle missing required keys in the definition
            print(f"ERROR: Missing required key {ke} in goods definition for '{good_id}'. Skipping.")
        except Exception as e:
            # Handle other errors during Good creation
            print(f"ERROR: Could not create good '{good_id}' from definition: {e}. Skipping.")

    # Critical check: Ensure at least one good was loaded successfully
    if not world.goods:
        print("ERROR: No valid goods were loaded. Cannot continue.")
        sys.exit(1)
    print(f"Loaded {len(world.goods)} goods.")

    # --- Load Recipes ---
    print(f"Attempting to load recipes from: {recipe_file}")
    try:
        with open(recipe_file, 'r') as f:
            recipes_data = json.load(f)
        print(f"Successfully loaded recipes from {recipe_file}")

        # Iterate through recipes defined in the JSON file
        for good_id, recipe_info in recipes_data.items():
            # Check if the good for this recipe exists in the world
            if good_id in world.goods:
                good = world.goods[good_id]
                # Only add recipes to goods marked as producible
                if good.is_producible:
                    try:
                        # Use dictionary unpacking to pass recipe details to the add_recipe method
                        good.add_recipe(**recipe_info)
                    except Exception as e:
                        # Handle errors during recipe addition (e.g., invalid format)
                        print(f"ERROR: Failed to add recipe for '{good_id}': {e}")
                # else: (Optional warning if trying to add recipe to non-producible good)
                #    print(f"WARN: Good '{good_id}' is not marked as producible, skipping recipe addition.")
            # else: (Optional warning if recipe exists for an unknown good ID)
            #     print(f"WARN: Recipe found for unknown good ID '{good_id}'. Skipping.")
    except FileNotFoundError:
        # Handle missing recipe file gracefully
        print(f"WARN: Recipe file '{recipe_file}' not found. No recipes loaded.")
    except json.JSONDecodeError:
        # Handle invalid JSON format in recipe file
        print(f"ERROR: Could not decode JSON from '{recipe_file}'. Check format.")
    except Exception as e:
        # Catch any other unexpected errors during recipe loading
        print(f"ERROR: An unexpected error occurred loading recipes: {e}")

    # --- Define Settlements ---
    print("Defining initial settlements...")
    # Get necessary parameters from sim_params for settlement creation consistency
    storage_per_pop = sim_params.get('storage_capacity_per_pop', 10.0)
    labor_per_pop = sim_params.get('labor_per_pop', 0.5)
    default_wealth = sim_params.get('settlement_default_initial_wealth', 500)
    city_pop_threshold = sim_params.get('city_population_threshold', 150)
    city_storage_mult = sim_params.get('city_storage_multiplier', 1.5)

    # List to hold settlement objects before adding them to the world
    settlements_to_add = []

    # Define the initial settlements, now including the z coordinate.
    # FUTURE: This section will need significant changes to define initial internal buildings and agent populations.
    settlements_to_add.append(Settlement(
        id='A', name='Farmstead', region_id='R1', population=100, terrain_type='Grassland',
        storage_capacity_per_pop=storage_per_pop, labor_per_pop=labor_per_pop,
        default_initial_wealth=default_wealth, city_population_threshold=city_pop_threshold,
        city_storage_multiplier=city_storage_mult,
        x=100, y=100, z=0 # Set Z coordinate
    ))
    settlements_to_add.append(Settlement(
        id='B', name='Logger\'s Camp', region_id='R1', population=60, terrain_type='Forest',
        storage_capacity_per_pop=storage_per_pop, labor_per_pop=labor_per_pop,
        default_initial_wealth=default_wealth, city_population_threshold=city_pop_threshold,
        city_storage_multiplier=city_storage_mult,
        x=100, y=300, z=5 # Set Z coordinate (slightly elevated)
    ))
    settlements_to_add.append(Settlement(
        id='C', name='Mine Town', region_id='R2', population=80, terrain_type='Mountain',
        storage_capacity_per_pop=storage_per_pop, labor_per_pop=labor_per_pop,
        default_initial_wealth=default_wealth, city_population_threshold=city_pop_threshold,
        city_storage_multiplier=city_storage_mult,
        x=400, y=100, z=20 # Set Z coordinate (higher elevation)
    ))
    settlements_to_add.append(Settlement(
        id='D', name='Craftburg', region_id='R2', population=120, terrain_type='Hills',
        storage_capacity_per_pop=storage_per_pop, labor_per_pop=labor_per_pop,
        default_initial_wealth=default_wealth, city_population_threshold=city_pop_threshold,
        city_storage_multiplier=city_storage_mult,
        initial_wealth=1000, x=400, y=300, z=10 # Set Z coordinate
    ))
    settlements_to_add.append(Settlement(
        id='E', name='Metropolis', region_id='R2', population=200, terrain_type='Plains',
        storage_capacity_per_pop=storage_per_pop, labor_per_pop=labor_per_pop,
        default_initial_wealth=default_wealth, city_population_threshold=city_pop_threshold,
        city_storage_multiplier=city_storage_mult,
        initial_wealth=1500, x=250, y=200, z=0 # Set Z coordinate
    ))

    # Add the defined Settlement objects to the World
    for s in settlements_to_add:
        world.add_settlement(s)

    # --- Add Initial Stock ---
    # Give some starting resources to specific settlements
    print("Adding initial stock to settlements...")
    try:
        # Check if good exists before trying to add it to prevent KeyErrors
        if 'seed' in world.goods: world.settlements['A'].add_to_storage(world.goods['seed'], quantity=5, tick=-1)
        if 'grain' in world.goods: world.settlements['A'].add_to_storage(world.goods['grain'], quantity=50, tick=-1)
        if 'wood' in world.goods: world.settlements['B'].add_to_storage(world.goods['wood'], quantity=30, tick=-1)
        if 'iron_ore' in world.goods: world.settlements['C'].add_to_storage(world.goods['iron_ore'], quantity=10, tick=-1)
        if 'wood' in world.goods: world.settlements['D'].add_to_storage(world.goods['wood'], quantity=10, tick=-1)
        if 'iron_ore' in world.goods: world.settlements['D'].add_to_storage(world.goods['iron_ore'], quantity=5, tick=-1)
        if 'grain' in world.goods: world.settlements['E'].add_to_storage(world.goods['grain'], quantity=100, tick=-1)
    except KeyError as ke:
        # This error might occur if a settlement ID ('A', 'B', etc.) used here is wrong
        # or if a good ID ('seed', 'grain', etc.) is missing from goods_definitions in config
        print(f"ERROR: Could not add initial stock. Settlement or Good ID '{ke}' not found.")
        print("       Check settlement IDs in world_setup.py and good IDs in config.json.")
    except Exception as e:
        # Catch other potential errors during stock addition
        print(f"ERROR: Failed to add initial stock: {e}")

    # --- Define Regions & Civilizations ---
    # Group settlements into regions and regions into civilizations
    print("Defining regions and civilizations...")
    region1 = Region('R1', 'Green Valley')
    region2 = Region('R2', 'Grey Peaks')

    # Assign settlements to regions based on their region_id
    for s in world.settlements.values():
        if s.region_id == 'R1':
            region1.add_settlement(s)
        elif s.region_id == 'R2':
            region2.add_settlement(s)
    # Add the created regions to the world
    world.add_region(region1)
    world.add_region(region2)

    # Create a civilization and add the regions to it
    civ1 = Civilization('C1', 'The Settlers')
    civ1.add_region(region1)
    civ1.add_region(region2)
    # Add the civilization to the world
    world.add_civilization(civ1)

    print(f"World setup complete with {len(world.settlements)} settlements.")
    # Return the fully configured and populated World object
    return world

# --- Optional: Test setup ---
# This block runs only when the script is executed directly (e.g., `python world_setup.py`)
if __name__ == "__main__":
    print("="*30)
    print("Executing world_setup.py directly for testing...")
    print("="*30)
    try:
        # Create a world instance using the setup function
        test_world = setup_world()

        # Print out details of the created world for verification
        print("-" * 20)
        print("Goods defined:")
        for good in test_world.goods.values():
            print(f"  - {good} (Producible: {good.is_producible}, Recipe: {'Yes' if good.recipe else 'No'})")

        print("-" * 20)
        print("Settlements created:")
        for settlement in test_world.get_all_settlements():
            # The settlement repr now includes the Z coordinate
            print(f"  - {settlement} (Storage Cap: {settlement.storage_capacity:.0f}, Labor Pool: {settlement.max_labor_pool:.1f})")
            # Optionally print initial inventory
            # print(f"    Inv: Bulk{dict(settlement.bulk_storage)}, Items{dict(settlement.item_storage)}")


        print("-" * 20)
        print("Regions created:")
        for region in test_world.regions.values():
            print(f"  - {region.name} (Settlements: {[s.name for s in region.settlements]})")

        print("-" * 20)
        print("Setup test complete.")
        print("="*30)

    except Exception as e:
        # Catch any errors during the test setup
        print(f"\n--- ERROR DURING WORLD SETUP TEST ---")
        print(e)
        import traceback
        traceback.print_exc() # Print detailed traceback for debugging
        print("-" * 35)
