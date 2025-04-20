import json
import sys # Import sys to use sys.exit()
from collections import defaultdict, OrderedDict

# --- Import Core Logic Classes ---
# Assumes trade_logic.py is in the same directory
try:
    from trade_logic import World, Good, Settlement, Region, Civilization, ItemInstance
    # Removed import of INITIAL_WEALTH as Settlement class handles default
except ImportError as e:
    # Print a more specific error and exit if import fails
    print("-" * 50)
    print("FATAL ERROR: Cannot import classes from 'trade_logic.py'.")
    print(f"ImportError: {e}")
    print("Please ensure:")
    print("  1. 'trade_logic.py' exists in the same directory as 'world_setup.py'.")
    print("  2. You are running this script from that directory.")
    print("  3. 'trade_logic.py' does not contain syntax errors.")
    print("-" * 50)
    sys.exit(1) # Exit the script cleanly


# --- Simulation Setup Function ---
def setup_world(recipe_file="recipes.json"):
    """Creates and initializes a specific world state, loading recipes from JSON."""
    world = World()
    TERRAINS = ['Plains', 'Grassland', 'Forest', 'Hills', 'Mountain']

    # Define Goods (mark Seed as producible)
    good_wood = Good(id='wood', name='Wood', base_value=5, is_bulk=True, is_producible=True)
    good_ore = Good(id='iron_ore', name='Iron Ore', base_value=10, is_bulk=True, is_producible=True)
    good_seed = Good(id='seed', name='Seed', base_value=2, is_bulk=True, is_producible=True) # Now producible
    good_grain = Good(id='grain', name='Grain', base_value=8, is_bulk=True, is_producible=True)
    good_tools = Good(id='tools', name='Tools', base_value=50, is_bulk=False, is_producible=True)
    good_textiles = Good(id='textiles', name='Textiles', base_value=70, is_bulk=False) # Still not producible

    # Add Goods to World
    world.add_good(good_seed); world.add_good(good_wood); world.add_good(good_ore)
    world.add_good(good_grain); world.add_good(good_tools); world.add_good(good_textiles)

    # --- Load Recipes from JSON ---
    try:
        with open(recipe_file, 'r') as f:
            recipes_data = json.load(f)
        print(f"Loaded recipes from {recipe_file}")

        for good_id, recipe_info in recipes_data.items():
            if good_id in world.goods:
                good = world.goods[good_id]
                if good.is_producible:
                    good.add_recipe(**recipe_info)
                else:
                    print(f"INFO: Recipe found for non-producible good '{good_id}' in {recipe_file}. Ensure Good is marked is_producible=True if intended.")
            else:
                 print(f"WARN: Recipe found for unknown good '{good_id}' in {recipe_file}. Skipping.")

    except FileNotFoundError:
        print(f"ERROR: Recipe file '{recipe_file}' not found. No recipes loaded.")
    except json.JSONDecodeError:
         print(f"ERROR: Could not decode JSON from '{recipe_file}'. Check file format.")
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading recipes: {e}")
    # --- End Recipe Loading ---


    # Define Settlements for this specific world instance
    # Pass initial wealth explicitly if different from default
    settlement_a = Settlement('A', 'Farmstead', 'R1', 100, terrain_type='Grassland')
    settlement_b = Settlement('B', 'Logger\'s Camp', 'R1', 60, terrain_type='Forest')
    settlement_c = Settlement('C', 'Mine Town', 'R2', 80, terrain_type='Mountain')
    settlement_d = Settlement('D', 'Craftburg', 'R2', 120, terrain_type='Hills', initial_wealth=1000)
    settlement_e = Settlement('E', 'Metropolis', 'R2', 200, terrain_type='Plains', initial_wealth=1500)

    # Add initial stock (example starting conditions)
    settlement_a.add_to_storage(good_seed, quantity=5, tick=-1)
    settlement_a.add_to_storage(good_grain, quantity=50, tick=-1)
    settlement_b.add_to_storage(good_wood, quantity=30, tick=-1)
    settlement_c.add_to_storage(good_ore, quantity=10, tick=-1)
    settlement_d.add_to_storage(good_wood, quantity=10, tick=-1); settlement_d.add_to_storage(good_ore, quantity=5, tick=-1)
    # settlement_d.wealth = 1000 # Wealth set in constructor now
    settlement_e.add_to_storage(good_grain, quantity=100, tick=-1) # settlement_e.wealth set in constructor

    # Add Settlements to World
    world.add_settlement(settlement_a); world.add_settlement(settlement_b); world.add_settlement(settlement_c)
    world.add_settlement(settlement_d); world.add_settlement(settlement_e)

    # Define Regions and Civilizations (optional structure)
    region1 = Region('R1', 'Green Valley')
    region1.add_settlement(settlement_a); region1.add_settlement(settlement_b)
    region2 = Region('R2', 'Grey Peaks')
    region2.add_settlement(settlement_c); region2.add_settlement(settlement_d); region2.add_settlement(settlement_e)
    world.add_region(region1); world.add_region(region2)

    civ1 = Civilization('C1', 'The Settlers')
    civ1.add_region(region1); civ1.add_region(region2)
    world.add_civilization(civ1)

    print(f"World setup complete with {len(world.settlements)} settlements.")
    return world

# --- Optional: Allow running this file directly to test setup ---
if __name__ == "__main__":
    print("Testing world setup...")
    # Wrap the test execution in a try block as well
    try:
        test_world = setup_world()
        print("-" * 20)
        print("Goods defined:")
        for good in test_world.goods.values():
            print(f"  - {good.name} ({good.id}), BaseVal: {good.base_value}, Producible: {good.is_producible}")
            if good.recipe:
                print(f"    Recipe: {good.recipe}")
        print("-" * 20)
        print("Settlements created:")
        for settlement in test_world.get_all_settlements():
            print(f"  - {settlement.name} ({settlement.id}), Terrain: {settlement.terrain_type}, Pop: {settlement.population}")
            print(f"    Initial Wealth: {settlement.wealth}")
        print("-" * 20)
        print("Setup test complete.")
    except Exception as e:
        # Catch any errors during the test setup itself
        print(f"\n--- ERROR DURING WORLD SETUP TEST ---")
        print(e)
        import traceback
        traceback.print_exc()
        print("------------------------------------")

