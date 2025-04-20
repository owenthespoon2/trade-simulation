import json
import sys
from collections import defaultdict, OrderedDict
import random

# --- Import Core Logic Classes ---
try:
    from trade_logic import World, Good, Settlement, Region, Civilization, ItemInstance
except ImportError as e:
    print("-" * 50); print("FATAL ERROR: Cannot import classes from 'trade_logic.py'."); print(f"ImportError: {e}"); print("Please ensure 'trade_logic.py' exists and is runnable."); print("-" * 50); sys.exit(1)

# --- Simulation Setup Function ---
def setup_world(config_file="config.json", recipe_file="recipes.json"):
    """Creates and initializes world state, loading parameters, goods, and recipes from JSON."""

    # --- Load Configuration ---
    try:
        with open(config_file, 'r') as f: config_data = json.load(f)
        sim_params = config_data.get("simulation_parameters", {})
        goods_defs = config_data.get("goods_definitions", {})
        print(f"Loaded configuration from {config_file}")
    except FileNotFoundError:
        print(f"ERROR: Config file '{config_file}' not found. Using default parameters.")
        sim_params = { "price_sensitivity": 2.0, "storage_capacity_per_pop": 10.0, "max_trades_per_tick": 5, "labor_per_pop": 0.5, "trade_profit_margin_threshold": 1.05, "settlement_default_initial_wealth": 500, "base_consumption_rate": 0.1, "max_production_passes": 5, "min_price_multiplier": 0.1, "max_price_multiplier": 10.0, "city_population_threshold": 150, "city_storage_multiplier": 1.5, "storage_cost_per_unit": 0.01 }
        goods_defs = {}
    except json.JSONDecodeError: print(f"ERROR: Could not decode JSON from '{config_file}'. Check file format. Exiting."); sys.exit(1)
    except Exception as e: print(f"ERROR: An unexpected error occurred loading config: {e}. Exiting."); sys.exit(1)

    if not goods_defs: print("ERROR: No goods definitions found in config file or defaults. Cannot setup world."); sys.exit(1)

    # --- Initialize World with Parameters ---
    world = World(sim_params)

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
    try:
        with open(recipe_file, 'r') as f: recipes_data = json.load(f)
        print(f"Loaded recipes from {recipe_file}")
        for good_id, recipe_info in recipes_data.items():
            if good_id in world.goods:
                good = world.goods[good_id]
                if good.is_producible:
                    try: good.add_recipe(**recipe_info)
                    except Exception as e: print(f"ERROR: Failed to add recipe for '{good_id}': {e}")
            # else: (Optional warning)
    except FileNotFoundError: print(f"WARN: Recipe file '{recipe_file}' not found. No recipes loaded.")
    except json.JSONDecodeError: print(f"ERROR: Could not decode JSON from '{recipe_file}'. Check format.")
    except Exception as e: print(f"ERROR: An unexpected error occurred loading recipes: {e}")

    # --- Define Settlements ---
    storage_per_pop = sim_params.get('storage_capacity_per_pop', 10.0)
    labor_per_pop = sim_params.get('labor_per_pop', 0.5)
    default_wealth = sim_params.get('settlement_default_initial_wealth', 500)
    city_pop_threshold = sim_params.get('city_population_threshold', 150) # Get threshold
    city_storage_mult = sim_params.get('city_storage_multiplier', 1.5) # Get multiplier

    settlements_to_add = []

    # Define settlements, passing the required parameters for storage calculation
    settlements_to_add.append(Settlement('A', 'Farmstead', 'R1', 100, 'Grassland', storage_per_pop, labor_per_pop, default_wealth, city_pop_threshold, city_storage_mult, x=100, y=100))
    settlements_to_add.append(Settlement('B', 'Logger\'s Camp', 'R1', 60, 'Forest', storage_per_pop, labor_per_pop, default_wealth, city_pop_threshold, city_storage_mult, x=100, y=300))
    settlements_to_add.append(Settlement('C', 'Mine Town', 'R2', 80, 'Mountain', storage_per_pop, labor_per_pop, default_wealth, city_pop_threshold, city_storage_mult, x=400, y=100))
    settlements_to_add.append(Settlement('D', 'Craftburg', 'R2', 120, 'Hills', storage_per_pop, labor_per_pop, default_wealth, city_pop_threshold, city_storage_mult, initial_wealth=1000, x=400, y=300))
    settlements_to_add.append(Settlement('E', 'Metropolis', 'R2', 200, 'Plains', storage_per_pop, labor_per_pop, default_wealth, city_pop_threshold, city_storage_mult, initial_wealth=1500, x=250, y=200))

    # Add Lots of Little Settlements
    num_small_settlements = 10
    possible_terrains = ['Plains', 'Grassland', 'Forest', 'Hills']
    start_id_ord = ord('F')
    min_coord, max_coord = 50, 450
    min_dist_sq = 80**2 # <<< Increased minimum squared distance further

    existing_coords = [(s.x, s.y) for s in settlements_to_add]

    for i in range(num_small_settlements):
        settlement_id = chr(start_id_ord + i)
        name = f"Hamlet {settlement_id}"
        pop = random.randint(20, 50)
        terrain = random.choice(possible_terrains)
        region = random.choice(['R1', 'R2'])

        placed = False
        for _attempt in range(200): # Increase attempts slightly
            x = random.randint(min_coord, max_coord)
            y = random.randint(min_coord, max_coord)
            too_close = False
            for ex, ey in existing_coords:
                dist_sq = (x - ex)**2 + (y - ey)**2
                if dist_sq < min_dist_sq:
                    too_close = True; break
            if not too_close:
                settlements_to_add.append(Settlement(settlement_id, name, region, pop, terrain,
                                                     storage_per_pop, labor_per_pop, default_wealth,
                                                     city_pop_threshold, city_storage_mult, # Pass params
                                                     x=x, y=y))
                existing_coords.append((x, y))
                placed = True; break
        if not placed: print(f"WARN: Could not place small settlement {settlement_id} without overlap after 200 attempts.")

    # Add Settlements to World
    for s in settlements_to_add: world.add_settlement(s)

    # Add initial stock
    try:
        world.settlements['A'].add_to_storage(world.goods['seed'], quantity=5, tick=-1)
        world.settlements['A'].add_to_storage(world.goods['grain'], quantity=50, tick=-1)
        world.settlements['B'].add_to_storage(world.goods['wood'], quantity=30, tick=-1)
        world.settlements['C'].add_to_storage(world.goods['iron_ore'], quantity=10, tick=-1)
        world.settlements['D'].add_to_storage(world.goods['wood'], quantity=10, tick=-1)
        world.settlements['D'].add_to_storage(world.goods['iron_ore'], quantity=5, tick=-1)
        world.settlements['E'].add_to_storage(world.goods['grain'], quantity=100, tick=-1)
        for s in world.settlements.values():
            if s.id >= 'F' and s.terrain_type == 'Forest': s.add_to_storage(world.goods['wood'], quantity=1, tick=-1)
            if s.id >= 'F' and s.terrain_type == 'Hills': s.add_to_storage(world.goods['seed'], quantity=1, tick=-1)
    except KeyError as ke: print(f"ERROR: Could not add initial stock. Good '{ke}' not found.")
    except Exception as e: print(f"ERROR: Failed to add initial stock: {e}")

    # Define Regions and Civilizations
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
    # (Test code remains the same)
    print("Testing world setup...")
    try:
        test_world = setup_world()
        print("-" * 20); print("Goods defined:");
        for good in test_world.goods.values(): print(f"  - {good}")
        print("-" * 20); print("Settlements created:");
        for settlement in test_world.get_all_settlements(): print(f"  - {settlement} (Storage Cap: {settlement.storage_capacity})") # Show capacity
        print("-" * 20); print("Setup test complete.")
    except Exception as e:
        print(f"\n--- ERROR DURING WORLD SETUP TEST ---"); print(e)
        import traceback; traceback.print_exc(); print("-" * 35)

