import random
import uuid
import math
import os
import time
from collections import defaultdict, OrderedDict
import json

# ==============================================================================
# FILE INDEX
# ==============================================================================
# - Data Structures (Good, ItemInstance) : Line 19
# - Settlement Class                      : Line 59
#   - __init__                            : Line 62  (Added production_this_tick)
#   - update_derived_stats                : Line 96
#   - Storage Management (add/remove/get) : Line 115
#   - produce                             : Line 161 (Added production tracking logic)
#   - consume                             : Line 243
#   - update_prices                       : Line 273
# - Region Class                          : Line 301
# - Civilization Class                    : Line 307
# - World Class                           : Line 313
#   - __init__                            : Line 315
#   - Entity Management (add/get)         : Line 330
#   - get_global_good_totals              : Line 338 (NEW METHOD)
#   - find_trade_opportunities            : Line 351
#   - execute_trades                      : Line 394
#   - _calculate_distance                 : Line 497
#   - simulation_step                     : Line 502
#     - Core Economic Phases              : Line 513
#     - Trade Phase                       : Line 525
#     - Upkeep Phase                      : Line 535
#     - Abandonment Check Phase           : Line 545
#     - Migration Phase                   : Line 571
# ==============================================================================


# ==============================================================================
# Data Structures
# ==============================================================================

class Good:
    """
    Represents a type of good that can be produced, traded, and consumed
    within the simulation. Goods have inherent properties like base value
    and whether they are treated as bulk items or unique instances.
    """
    def __init__(self, id, name, base_value, is_bulk=True, is_producible=False):
        """
        Initializes a Good.

        Args:
            id (str): Unique identifier for the good (e.g., 'wood', 'grain').
            name (str): Human-readable name (e.g., 'Wood', 'Grain').
            base_value (float): Intrinsic value used for price calculations.
            is_bulk (bool, optional): True if goods stack (quantity matters),
                                      False if treated as unique items (like tools). Defaults to True.
            is_producible (bool, optional): True if this good can be created via a recipe.
                                           Defaults to False.
        """
        self.id = id
        self.name = name
        self.base_value = base_value
        self.is_bulk = is_bulk
        self.is_producible = is_producible
        self.recipe = None # Stores production recipe if is_producible

    def __repr__(self):
        """String representation of the Good."""
        return f"Good({self.name})"

    def add_recipe(self, inputs, outputs, labor, required_terrain=None, wealth_cost=0):
        """
        Adds a production recipe to a producible good.

        Args:
            inputs (dict): Dictionary of {good_id: quantity} required as input.
            outputs (dict): Dictionary of {good_id: quantity} produced.
            labor (float): Amount of labor units required for one production cycle.
            required_terrain (list, optional): List of terrain types where this recipe can be used.
                                              Defaults to None (no terrain requirement).
            wealth_cost (float, optional): Direct cost in wealth to perform one production cycle.
                                          Defaults to 0.

        Raises:
            TypeError: If inputs or outputs are not dictionaries.
            ValueError: If outputs dictionary is empty.
        """
        if not self.is_producible:
            print(f"WARN: Cannot add recipe to non-producible good: {self.name}")
            return
        # Input validation
        if not isinstance(inputs, dict): raise TypeError(f"Recipe inputs for {self.id} must be a dict")
        if not isinstance(outputs, dict): raise TypeError(f"Recipe outputs for {self.id} must be a dict")
        if not outputs: raise ValueError(f"Recipe for {self.id} must have outputs")

        self.recipe = {
            'inputs': inputs,
            'outputs': outputs,
            'labor': float(labor),
            'required_terrain': required_terrain,
            'wealth_cost': float(wealth_cost)
        }

class ItemInstance:
    """
    Represents a specific instance of a non-bulk good. This allows tracking
    the origin, trade history, and potentially quality of unique items like tools.
    """
    def __init__(self, good_id, origin_settlement_id, quantity=1, quality=1.0):
        """
        Initializes an ItemInstance.

        Args:
            good_id (str): The ID of the Good this instance represents.
            origin_settlement_id (str): The ID of the settlement where this item was created.
            quantity (float, optional): The amount contained in this instance. Defaults to 1.
                                       Mainly relevant if non-bulk items can be bundled.
            quality (float, optional): A potential metric for item quality (e.g., tool durability).
                                      Defaults to 1.0.
        """
        self.instance_id = str(uuid.uuid4()) # Unique ID for this specific item instance
        self.good_id = good_id
        self.origin_settlement_id = origin_settlement_id
        self.current_location_settlement_id = origin_settlement_id # Tracks current holder
        self.quantity = quantity
        self.quality = quality
        self.trade_history = [] # List of (settlement_id, price, tick) tuples tracking trades

    def __repr__(self):
        """String representation of the ItemInstance."""
        history_summary = f", History: {len(self.trade_history)} steps" if self.trade_history else ""
        return (f"Item(ID: {self.instance_id[:4]}..., Good: {self.good_id}, "
                f"Origin: {self.origin_settlement_id}, Loc: {self.current_location_settlement_id}, "
                f"Qty: {self.quantity:.1f}{history_summary})")

# ==============================================================================
# Settlement Class
# ==============================================================================
# FUTURE: Refactor Settlement to act as a container/manager for internal Building and Agent objects.
class Settlement:
    """
    Represents a settlement (village, town, city) as the core economic unit.
    Manages population, resources (storage), production, consumption, wealth,
    local prices, and its position in the world.
    Acts as the primary 'agent' in the current simulation design.
    """
    # FUTURE: Replace 'population' int with a collection of Agent objects, each with specialized roles/state.
    # FUTURE: Decide if wealth/storage remains central (Town Hall) or becomes distributed among internal Agents/Buildings.
    def __init__(self, id, name, region_id, population, terrain_type,
                 storage_capacity_per_pop, labor_per_pop, default_initial_wealth,
                 city_population_threshold, city_storage_multiplier, # Base params from config
                 initial_wealth=None, x=0, y=0, z=0): # Position including Z
        """
        Initializes a Settlement.

        Args:
            id (str): Unique identifier for the settlement.
            name (str): Human-readable name.
            region_id (str): ID of the Region this settlement belongs to.
            population (int): Initial population.
            terrain_type (str): Type of terrain the settlement is on (e.g., 'Forest', 'Plains').
            storage_capacity_per_pop (float): Base storage capacity per population unit.
            labor_per_pop (float): Base labor generated per population unit per tick.
            default_initial_wealth (float): Default starting wealth if not specified.
            city_population_threshold (int): Population level at which a settlement gains city bonuses.
            city_storage_multiplier (float): Multiplier applied to storage capacity for cities.
            initial_wealth (float, optional): Specific starting wealth. Defaults to default_initial_wealth.
            x (float, optional): X coordinate. Defaults to 0.
            y (float, optional): Y coordinate. Defaults to 0.
            z (float, optional): Z coordinate. Defaults to 0.
        """
        self.id = id
        self.name = name
        self.region_id = region_id
        self.population = max(1, int(population)) # Ensure population is at least 1 integer
        self.terrain_type = terrain_type
        self.x = float(x)
        self.y = float(y)
        self.z = float(z) # Store Z coordinate

        # Storage: Separate dicts for bulk goods (float quantity) and item instances (list of ItemInstance)
        self.bulk_storage = defaultdict(float)
        self.item_storage = defaultdict(list)

        # Economic state
        self.consumption_needs = defaultdict(lambda: 1.0) # Modifier for demand (potential future use)
        self.local_prices = {} # Calculated prices {good_id: price} updated each tick
        self.wealth = float(initial_wealth if initial_wealth is not None else default_initial_wealth)
        self.market_level = 1 # Potential future use for market size/efficiency
        self.log = [] # Short log of recent events for this settlement (e.g., trade failures)

        # Production Tracking <<< NEW in Phase 1.7 >>>
        # Stores {good_id: quantity} produced in the current tick's production phase
        self.production_this_tick = defaultdict(float)

        # Store base parameters from config needed for dynamic calculation based on population
        self._storage_capacity_per_pop = float(storage_capacity_per_pop)
        self._labor_per_pop = float(labor_per_pop)
        self._city_pop_threshold = int(city_population_threshold)
        self._city_storage_multiplier = float(city_storage_multiplier)

        # Initial calculation of derived stats (updated by update_derived_stats)
        self.max_labor_pool = 0.0
        self.storage_capacity = 0.0
        self.current_labor_pool = 0.0 # Labor available this tick
        self.update_derived_stats() # Calculate initial values based on starting pop

        # State for Abandonment tracking
        self.ticks_below_wealth_threshold = 0
        self.is_abandoned = False # Flag to mark for removal by World

        # FUTURE: Internal buildings/agents might need relative coordinates within the settlement area.

    def update_derived_stats(self):
        """
        Recalculates settlement statistics that depend on population, such as
        labor pool and storage capacity. Called after population changes (e.g., migration).
        """
        self.population = max(1, self.population) # Ensure population doesn't drop below 1

        # Calculate max labor pool based on population
        self.max_labor_pool = self.population * self._labor_per_pop
        # Replenish available labor pool when stats update (represents new labor becoming available)
        # Note: Labor pool replenishment might be better handled at the start of the tick/production phase
        self.current_labor_pool = self.max_labor_pool

        # Recalculate storage capacity based on population and city status
        base_capacity = self.population * self._storage_capacity_per_pop
        if self.population >= self._city_pop_threshold:
            # Apply city bonus multiplier
            self.storage_capacity = base_capacity * self._city_storage_multiplier
        else:
            self.storage_capacity = base_capacity

    def __repr__(self):
        """String representation of the Settlement, including Z coordinate."""
        return (f"Settlement({self.name}, Pop: {self.population}, "
                f"Wealth: {self.wealth:.0f}, Terrain: {self.terrain_type}, "
                f"Pos:({self.x:.0f},{self.y:.0f},{self.z:.0f}))") # Show coords as int for brevity

    def add_log(self, message, tick):
        """Adds a timestamped message to the settlement's short event log."""
        self.log.append(f"T{tick}: {message}")
        self.log = self.log[-10:] # Keep only the last 10 messages

    # --- Storage Management ---
    def get_total_stored(self, good_id):
        """
        Returns the total quantity of a specific good in storage, summing
        bulk storage and quantities from all relevant item instances.

        Args:
            good_id (str): The ID of the good to query.

        Returns:
            float: Total quantity of the good stored.
        """
        bulk_qty = self.bulk_storage.get(good_id, 0.0)
        item_qty = sum(item.quantity for item in self.item_storage.get(good_id, []))
        return bulk_qty + item_qty

    def get_current_storage_load(self):
        """
        Returns the total quantity of ALL goods currently stored, summing
        all bulk goods and all item instance quantities. Used to check against
        storage capacity.

        Returns:
            float: Total quantity of all goods stored.
        """
        total_bulk = sum(self.bulk_storage.values())
        total_items = sum(item.quantity for items in self.item_storage.values() for item in items)
        return total_bulk + total_items

    def add_to_storage(self, good, quantity=None, item_instance=None, tick=0):
        """
        Adds goods or a specific item instance to the settlement's storage,
        respecting storage capacity limits.

        Args:
            good (Good): The Good object to add (required if quantity is specified).
            quantity (float, optional): The amount of the good to add. Used for bulk goods
                                       or creating new instances of non-bulk goods.
            item_instance (ItemInstance, optional): A specific ItemInstance to add (used for non-bulk goods).
            tick (int, optional): Current simulation tick for logging.

        Returns:
            float: The actual quantity added (might be less than requested due to capacity).
        """
        current_load = self.get_current_storage_load()
        available_capacity = max(0.0, self.storage_capacity - current_load)
        added_qty = 0.0

        # Check if storage is effectively full (using a small tolerance)
        if available_capacity <= 1e-6:
            return 0.0 # Cannot add anything

        if item_instance: # Adding a specific non-bulk item instance (e.g., from trade)
            needed_capacity = item_instance.quantity
            if needed_capacity <= available_capacity:
                self.item_storage[item_instance.good_id].append(item_instance)
                item_instance.current_location_settlement_id = self.id # Update item location
                added_qty = item_instance.quantity
            else:
                 # Not enough space for the whole item instance.
                 # This should ideally be prevented by checks in execute_trades.
                pass
        elif good and quantity is not None: # Adding a quantity of a good (bulk or creating new non-bulk)
            amount_to_add = min(quantity, available_capacity)
            if amount_to_add > 1e-6: # Only add if it's a meaningful amount
                if good.is_bulk:
                    self.bulk_storage[good.id] += amount_to_add
                else:
                    # Create a new ItemInstance if adding non-bulk this way
                    new_instance = ItemInstance(good.id, self.id, quantity=amount_to_add)
                    self.item_storage[good.id].append(new_instance)
                added_qty = amount_to_add

        return added_qty

    def remove_from_storage(self, good_id, quantity, tick=0):
        """
        Removes a specified quantity of a good from storage. Prioritizes bulk storage,
        then consumes item instances if necessary.

        Args:
            good_id (str): The ID of the good to remove.
            quantity (float): The amount to remove.
            tick (int, optional): Current simulation tick for logging.

        Returns:
            tuple: (quantity_removed, consumed_instances)
                   quantity_removed (float): The actual amount removed (might be less than requested).
                   consumed_instances (list): List of ItemInstance objects representing the portions
                                             of non-bulk items consumed (useful for tracking trade history).
        """
        removed_qty = 0.0
        consumed_instances = [] # Stores representations of consumed ItemInstance parts

        # 1. Remove from bulk storage first
        if good_id in self.bulk_storage:
            take_from_bulk = min(quantity, self.bulk_storage[good_id])
            self.bulk_storage[good_id] -= take_from_bulk
            removed_qty += take_from_bulk
            if self.bulk_storage[good_id] < 1e-6: # Clean up if storage is empty
                del self.bulk_storage[good_id]

        # 2. If more is needed, remove from item storage
        remaining_needed = quantity - removed_qty
        if remaining_needed > 1e-6 and good_id in self.item_storage:
            items_list = self.item_storage[good_id]
            indices_to_remove = [] # Track indices of fully consumed item instances

            # Iterate through available item instances of this good
            for i, item in enumerate(items_list):
                if remaining_needed <= 1e-6: break # Stop if requirement met

                take_from_item = min(remaining_needed, item.quantity)

                # Create a temporary ItemInstance object to represent the consumed portion
                consumed_instance_part = ItemInstance(
                    good_id=item.good_id,
                    origin_settlement_id=item.origin_settlement_id,
                    quantity=take_from_item,
                    quality=item.quality
                )
                consumed_instance_part.instance_id = item.instance_id # Preserve original ID
                consumed_instance_part.trade_history = item.trade_history[:] # Copy history
                consumed_instances.append(consumed_instance_part)

                # Update the original item instance
                item.quantity -= take_from_item
                removed_qty += take_from_item
                remaining_needed -= take_from_item

                # Mark item for removal if fully consumed
                if item.quantity < 1e-6:
                    indices_to_remove.append(i)

            # Remove fully consumed items from storage (in reverse order)
            for i in sorted(indices_to_remove, reverse=True):
                del items_list[i]

            # Clean up the item storage dict if the list becomes empty
            if not self.item_storage[good_id]:
                del self.item_storage[good_id]

        return removed_qty, consumed_instances

    # --- Economic Actions ---
    # FUTURE: Delegate production logic to specific internal Agent/Building objects.
    def produce(self, all_goods_dict, params, world_tick):
        """
        Attempts to produce goods based on available recipes, labor, resources,
        terrain requirements, and wealth buffer. Tracks produced amounts.
        """
        # Get parameters from world config
        max_production_passes = params.get('max_production_passes', 5)
        production_wealth_buffer = params.get('production_wealth_buffer', 0.0)

        # <<< Clear production tracker for this tick >>>
        self.production_this_tick.clear()

        # --- Production Halt Check ---
        if self.wealth < production_wealth_buffer:
            return # Exit if wealth is too low

        # Replenish the labor pool available for this tick's production phase
        self.current_labor_pool = self.max_labor_pool

        # --- Production Loop (Multiple Passes) ---
        for _pass in range(max_production_passes):
            production_possible_in_pass = False # Track if any production occurs

            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            if not producible_goods: break # Exit if no producible goods

            producible_items = list(producible_goods.items())
            random.shuffle(producible_items) # Shuffle order

            for good_id, good in producible_items:
                recipe = good.recipe

                # --- Check Feasibility (Terrain, Labor, Wealth Cost, Inputs) ---
                if recipe['required_terrain'] and self.terrain_type not in recipe['required_terrain']: continue
                if self.current_labor_pool < recipe['labor']: continue
                if self.wealth < recipe['wealth_cost']: continue
                inputs_available = True
                required_inputs = recipe['inputs']
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        if self.get_total_stored(input_good_id) < input_qty:
                            inputs_available = False; break
                    if not inputs_available: continue

                # --- Attempt Production Transaction ---
                original_labor = self.current_labor_pool
                original_wealth = self.wealth
                temp_input_storage_state = {}
                temp_output_storage_state = {} # Track initial state of outputs too

                # 1. Consume Labor & Wealth Cost (tentative)
                self.current_labor_pool -= recipe['labor']
                self.wealth -= recipe['wealth_cost']

                # 2. Consume Inputs (tentative)
                inputs_consumed_successfully = True
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        temp_input_storage_state[input_good_id] = self.get_total_stored(input_good_id)
                        removed_qty, _ = self.remove_from_storage(input_good_id, input_qty, tick=world_tick)
                        if removed_qty < input_qty * 0.999:
                            inputs_consumed_successfully = False
                            # Revert state
                            self.current_labor_pool = original_labor; self.wealth = original_wealth
                            for gid, initial_qty in temp_input_storage_state.items():
                                 current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                                 if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                            break
                    if not inputs_consumed_successfully: continue

                # 3. Add Outputs (tentative) & Track Production
                outputs_produced_successfully = True
                actual_added_quantities = {} # Store actual added amount for tracking
                for output_good_id, output_qty in recipe['outputs'].items():
                    output_good = all_goods_dict[output_good_id]
                    temp_output_storage_state[output_good_id] = self.get_total_stored(output_good_id)
                    added_qty = self.add_to_storage(output_good, quantity=output_qty, tick=world_tick)
                    actual_added_quantities[output_good_id] = added_qty # Store actual amount added
                    if added_qty < output_qty * 0.999: # Check if storage was full
                        outputs_produced_successfully = False
                        # Revert state
                        self.current_labor_pool = original_labor; self.wealth = original_wealth
                        # Add back inputs
                        for gid, initial_qty in temp_input_storage_state.items():
                             current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                             if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                        # Remove partially added outputs
                        for gid, initial_qty in temp_output_storage_state.items():
                            current_qty = self.get_total_stored(gid); qty_to_remove = current_qty - initial_qty
                            if qty_to_remove > 1e-6: self.remove_from_storage(gid, qty_to_remove)
                        break # Stop adding outputs for this recipe
                if not outputs_produced_successfully: continue

                # --- Production Success ---
                # <<< Update Production Tracker using actual added quantities >>>
                for output_good_id, added_qty in actual_added_quantities.items():
                    if added_qty > 1e-6:
                        self.production_this_tick[output_good_id] += added_qty

                production_possible_in_pass = True # Mark production occurred

            # If no production happened in the entire pass, stop early
            if not production_possible_in_pass: break

    # FUTURE: Delegate consumption logic to internal Agent/Building objects.
    def consume(self, goods_dict, params, world_tick):
        """
        Simulates consumption of goods by the settlement's population based on
        needs, population size, and city status.
        """
        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            if good_id in ['iron_ore', 'seed']: continue # Skip raw materials

            consume_this = False
            if good_id == 'bread' and is_city: consume_this = True
            elif good_id != 'bread' and not (good_id == 'grain' and is_city): consume_this = True

            if consume_this:
                demand_modifier = self.consumption_needs[good_id]
                amount_needed = (base_consumption_rate * self.population * demand_modifier
                                 * (1 + random.uniform(-0.1, 0.1)))
                amount_needed = max(0, amount_needed)

                if amount_needed > 0.01:
                    available = self.get_total_stored(good_id)
                    amount_to_consume = min(amount_needed, available)
                    if amount_to_consume > 0.01:
                        removed_qty, _ = self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)
                        # Optional: Track unmet needs if removed_qty < amount_needed * 0.9

    # FUTURE: Delegate price setting to a central 'Market' building/entity.
    def update_prices(self, goods_dict, params, world_tick):
        """
        Updates local prices for all goods based on the ratio of current supply
        to estimated demand. Prices are clamped within min/max multipliers.
        """
        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        price_sensitivity = params.get('price_sensitivity', 2.0)
        min_price_multiplier = params.get('min_price_multiplier', 0.1)
        max_price_multiplier = params.get('max_price_multiplier', 10.0)
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            supply = self.get_total_stored(good_id)
            supply = max(supply, 0.01) # Avoid division by zero

            demand_estimate = 0.01 # Baseline demand
            if good_id not in ['iron_ore', 'seed']:
                 if good_id == 'bread' and is_city:
                     demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
                 elif good_id != 'bread' and not (good_id == 'grain' and is_city):
                     demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
            demand_estimate = max(demand_estimate, 0.01)

            ratio = supply / demand_estimate
            price_modifier = math.pow(ratio, -price_sensitivity)

            min_price = good.base_value * min_price_multiplier
            max_price = good.base_value * max_price_multiplier
            new_price = good.base_value * price_modifier
            self.local_prices[good_id] = max(min_price, min(new_price, max_price))

# ==============================================================================
# Region Class
# ==============================================================================
class Region:
    """Represents a geographical region containing multiple settlements."""
    def __init__(self, id, name, resource_modifiers=None):
        """Initializes a Region."""
        self.id = id
        self.name = name
        self.resource_modifiers = resource_modifiers if resource_modifiers else {}
        self.settlements = []

    def add_settlement(self, settlement):
        """Adds a settlement object to this region's list."""
        self.settlements.append(settlement)

# ==============================================================================
# Civilization Class
# ==============================================================================
class Civilization:
    """Represents a civilization or faction encompassing multiple regions (future use)."""
    def __init__(self, id, name):
        """Initializes a Civilization."""
        self.id = id
        self.name = name
        self.regions = []

    def add_region(self, region):
        """Adds a region object to this civilization's list."""
        self.regions.append(region)

# ==============================================================================
# World Class
# ==============================================================================
class World:
    """
    Manages the overall simulation state and orchestrates the simulation loop.
    Contains all entities (goods, settlements, regions, etc.) and global parameters.
    """
    def __init__(self, sim_params):
        """Initializes the World object."""
        self.tick = 0 # Simulation time counter
        self.goods = OrderedDict() # {good_id: Good object}
        self.settlements = OrderedDict() # {settlement_id: Settlement object}
        self.regions = OrderedDict() # {region_id: Region object}
        self.civilizations = OrderedDict() # {civ_id: Civilization object}
        self.trade_routes = {} # Potential future use

        # Logging and tracking lists for UI/analysis, cleared each tick
        self.recent_trades_log = []
        self.executed_trade_details_this_tick = []
        self.potential_trades_this_tick = []
        self.failed_trades_this_tick = []
        self.migration_details_this_tick = [] # Stores migration events this tick

        self.params = sim_params # Dictionary of simulation parameters from config
        print(f"World initialized with parameters: {self.params}")

    # --- Entity Management ---
    def add_good(self, good):
        """Adds a Good object to the world's dictionary."""
        self.goods[good.id] = good

    def add_settlement(self, settlement):
        """Adds a Settlement object to the world's dictionary."""
        self.settlements[settlement.id] = settlement

    def add_region(self, region):
        """Adds a Region object to the world's dictionary."""
        self.regions[region.id] = region

    def add_civilization(self, civilization):
        """Adds a Civilization object to the world's dictionary."""
        self.civilizations[civilization.id] = civilization

    def get_all_settlements(self):
        """Returns a list of all currently active (non-abandoned) Settlement objects."""
        return list(self.settlements.values())

    # --- Global State Calculation --- <<< NEW in Phase 1.7 >>>
    def get_global_good_totals(self):
        """
        Calculates the total amount of each good stored across all active
        settlements in the world.

        Returns:
            dict: A dictionary mapping {good_id: total_quantity} for all goods
                  that have a non-zero quantity somewhere in the world.
        """
        totals = defaultdict(float)
        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]
        # Iterate through all known goods to ensure all are checked
        for good_id in self.goods.keys():
            total_qty = 0.0
            # Sum the stored amount from each active settlement
            for settlement in active_settlements:
                total_qty += settlement.get_total_stored(good_id)
            # Only include goods that actually exist in the world (quantity > 0)
            if total_qty > 1e-6:
                totals[good_id] = total_qty
        return dict(totals) # Return as a standard dictionary

    # --- Trade Logic ---
    def find_trade_opportunities(self):
        """
        Identifies potential trade opportunities between all pairs of active
        settlements based on local price differences exceeding a profit margin threshold.

        Returns:
            list: A list of dictionaries representing viable trade opportunities,
                  sorted by profit per unit (descending).
        """
        self.potential_trades_this_tick.clear()
        opportunities_for_execution = []

        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]
        price_threshold_multiplier = self.params.get('trade_profit_margin_threshold', 1.05)

        for i in range(len(active_settlements)):
            for j in range(i + 1, len(active_settlements)):
                settlement_a = active_settlements[i]
                settlement_b = active_settlements[j]

                for good_id, good in self.goods.items():
                    price_a = settlement_a.local_prices.get(good_id)
                    price_b = settlement_b.local_prices.get(good_id)

                    if price_a is None or price_b is None: continue
                    if price_a <= 1e-6 or price_b <= 1e-6: continue # Skip non-positive prices

                    profit, seller, buyer, qty_avail = 0, None, None, 0.0
                    seller_price, buyer_price = 0.0, 0.0

                    # Check B buying from A
                    if price_b > price_a * price_threshold_multiplier:
                        profit = price_b - price_a
                        seller, buyer = settlement_a, settlement_b
                        seller_price, buyer_price = price_a, price_b
                        qty_avail = seller.get_total_stored(good_id)
                    # Check A buying from B
                    elif price_a > price_b * price_threshold_multiplier:
                        profit = price_a - price_b
                        seller, buyer = settlement_b, settlement_a
                        seller_price, buyer_price = price_b, price_a
                        qty_avail = seller.get_total_stored(good_id)

                    if seller is not None and qty_avail > 1e-6:
                        potential_trade_qty = qty_avail # Max seller can offer
                        if not good.is_bulk and good_id in seller.item_storage:
                            items = seller.item_storage[good_id]
                            potential_trade_qty = items[0].quantity if items else 0
                        if potential_trade_qty < 1e-6: potential_trade_qty = 0

                        is_viable_prelim = (profit > 1e-6 and
                                           potential_trade_qty > 1e-6 and
                                           buyer.wealth > seller_price * 0.01) # Buyer needs to afford min qty

                        self.potential_trades_this_tick.append({
                            'seller_id': seller.id, 'buyer_id': buyer.id,
                            'seller_name': seller.name, 'buyer_name': buyer.name,
                            'good_id': good.id, 'good_name': good.name,
                            'seller_price': seller_price, 'buyer_price': buyer_price,
                            'profit_per_unit': profit, 'qty_avail': qty_avail,
                            'potential_qty': potential_trade_qty,
                            'is_viable_prelim': is_viable_prelim
                        })

                        if is_viable_prelim:
                            opportunities_for_execution.append({
                                'from': seller, 'to': buyer, 'good': good,
                                'profit_per_unit': profit,
                                'potential_qty': potential_trade_qty,
                                'seller_price': seller_price,
                                'buyer_price': buyer_price
                            })

        opportunities_for_execution.sort(key=lambda x: x['profit_per_unit'], reverse=True)
        return opportunities_for_execution

    def execute_trades(self, opportunities):
        """
        Attempts to execute trade opportunities, calculating actual quantity based
        on seller stock, buyer wealth, and buyer storage. Includes bulk trade logic.
        """
        trades_executed_log_entries = []
        self.executed_trade_details_this_tick.clear()
        self.failed_trades_this_tick.clear()

        trades_count = 0
        max_trades = self.params.get('max_trades_per_tick', 200)

        for i, trade in enumerate(opportunities):
            seller = trade['from']
            buyer = trade['to']
            good = trade['good']
            profit = trade['profit_per_unit']
            seller_potential_qty = trade['potential_qty'] # Max seller can offer
            seller_price = trade['seller_price']
            fail_reason = ""

            # Double check settlements still exist and are active
            if seller.id not in self.settlements or buyer.id not in self.settlements or seller.is_abandoned or buyer.is_abandoned:
                 fail_reason = "Settlement abandoned/removed"
                 self.failed_trades_this_tick.append({'seller_id': seller.id, 'buyer_id': buyer.id, 'good_id': good.id, 'fail_reason': fail_reason, 'tick': self.tick})
                 continue

            fail_log_base = { # Base info for logging failures
                'seller_id': seller.id, 'buyer_id': buyer.id, 'seller_name': seller.name, 'buyer_name': buyer.name,
                'good_id': good.id, 'good_name': good.name, 'seller_price': seller_price, 'buyer_price': trade['buyer_price'],
                'profit_per_unit': profit, 'potential_qty': seller_potential_qty, 'qty_avail': seller.get_total_stored(good.id)
            }

            # Check global trade limit
            if trades_count >= max_trades:
                fail_reason = "Skipped (Max Trades Reached)"
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                continue

            # --- Determine Actual Trade Quantity ---
            trade_qty = 0.0
            item_to_trade_instance_id = None

            if good.is_bulk:
                # === Bulk Trade Logic ===
                max_affordable_qty = float('inf')
                if seller_price > 1e-6: max_affordable_qty = buyer.wealth / seller_price
                buyer_available_storage = max(0.0, buyer.storage_capacity - buyer.get_current_storage_load())
                trade_qty = min(seller_potential_qty, max_affordable_qty, buyer_available_storage)
                # =======================
            else: # Non-bulk goods
                 if good.id in seller.item_storage and seller.item_storage[good.id]:
                    item_to_trade = seller.item_storage[good.id][0]
                    trade_qty = item_to_trade.quantity
                    item_to_trade_instance_id = item_to_trade.instance_id
                 else:
                    fail_reason = "Seller Lacks Non-Bulk Item (at execution)"
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                    continue

            # Ensure trade quantity is meaningful
            min_trade_qty = 0.01
            if trade_qty < min_trade_qty:
                 if seller_potential_qty < min_trade_qty: fail_reason = "Seller stock too low"
                 elif 'max_affordable_qty' in locals() and max_affordable_qty < min_trade_qty: fail_reason = "Buyer cannot afford min qty"
                 elif 'buyer_available_storage' in locals() and buyer_available_storage < min_trade_qty: fail_reason = "Buyer storage too low for min qty"
                 else: fail_reason = f"Calculated trade quantity ({trade_qty:.3f}) too small"
                 self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                 continue

            # --- Check Execution Feasibility (using calculated trade_qty) ---
            transaction_price = seller_price
            transaction_cost = transaction_price * trade_qty
            can_afford = buyer.wealth >= (transaction_cost - 1e-6) # Tolerance for float issues
            has_stock = seller.get_total_stored(good.id) >= (trade_qty - 1e-6) # Tolerance

            if not can_afford: fail_reason += f"Buyer Cannot Afford ({buyer.wealth:.1f} < {transaction_cost:.1f}); "
            if not has_stock: fail_reason += f"Seller Lacks Stock ({seller.get_total_stored(good.id):.1f} < {trade_qty:.1f}); "

            # --- Execute Transaction ---
            if can_afford and has_stock:
                removed_qty, consumed_instances = seller.remove_from_storage(good.id, trade_qty, tick=self.tick)

                if removed_qty < trade_qty * 0.999: # Verify removal
                    fail_reason += f"Failed Stock Removal ({removed_qty:.1f}/{trade_qty:.1f})"
                    # Try to return partially removed goods
                    if consumed_instances: seller.add_to_storage(good, item_instance=consumed_instances[0], tick=self.tick)
                    elif removed_qty > 1e-6: seller.add_to_storage(good, quantity=removed_qty, tick=self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})
                    continue

                item_instance_for_buyer = None # Prepare item if non-bulk
                if not good.is_bulk and consumed_instances:
                    original_instance_part = consumed_instances[0]
                    item_instance_for_buyer = ItemInstance(good_id=good.id, origin_settlement_id=original_instance_part.origin_settlement_id,
                                                           quantity=removed_qty, quality=original_instance_part.quality)
                    item_instance_for_buyer.trade_history = original_instance_part.trade_history[:]
                    item_instance_for_buyer.trade_history.append((seller.id, transaction_price, self.tick))
                    if item_to_trade_instance_id: item_instance_for_buyer.instance_id = item_to_trade_instance_id

                # Add to buyer's storage
                added_qty = buyer.add_to_storage(good, quantity=removed_qty if good.is_bulk else None,
                                                 item_instance=item_instance_for_buyer, tick=self.tick)

                if added_qty >= removed_qty * 0.999: # Verify addition
                    # --- Success! Finalize ---
                    final_cost = transaction_price * added_qty
                    seller.wealth += final_cost
                    buyer.wealth -= final_cost

                    trade_log_msg = (f"T{self.tick}: {seller.name} -> {buyer.name}, "
                                     f"{added_qty:.2f} {good.name} @ {transaction_price:.2f}")
                    trades_executed_log_entries.append(trade_log_msg)
                    self.executed_trade_details_this_tick.append({
                        'seller_id': seller.id, 'buyer_id': buyer.id, 'seller_name': seller.name, 'buyer_name': buyer.name,
                        'good_id': good.id, 'good_name': good.name, 'quantity': added_qty, 'seller_price': seller_price,
                        'buyer_price': trade['buyer_price'], 'profit_per_unit': profit, 'tick': self.tick
                    })
                    trades_count += 1
                else: # Failed to add (Buyer storage likely full)
                    fail_reason += f"Buyer Storage Failed (Avail: {max(0, buyer.storage_capacity - buyer.get_current_storage_load()):.1f})"
                    # Return goods to seller
                    item_to_return = consumed_instances[0] if not good.is_bulk and consumed_instances else None
                    if item_to_return and item_to_return.trade_history: item_to_return.trade_history.pop() # Remove failed trade from history
                    seller.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_to_return, tick=self.tick)
                    seller.add_log(f"Fail trade to {buyer.name} (storage?), {removed_qty:.1f} {good.name} returned", self.tick)
                    buyer.add_log(f"Fail trade from {seller.name} (storage full?)", self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})
            else: # Failed initial check (affordability or stock)
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})

        self.recent_trades_log = trades_executed_log_entries + self.recent_trades_log
        self.recent_trades_log = self.recent_trades_log[:10]

    # --- Utility Methods ---
    def _calculate_distance(self, s1, s2):
        """Calculate Euclidean distance between two settlements in 3D space."""
        return math.sqrt((s1.x - s2.x)**2 + (s1.y - s2.y)**2 + (s1.z - s2.z)**2)

    # ==========================================================================
    # Main Simulation Step
    # ==========================================================================
    # FUTURE: Add simulation phases for Agent actions (pathfinding, task execution) and Building management.
    def simulation_step(self):
        """
        Executes one full tick of the simulation cycle. Orchestrates all phases.
        """
        self.tick += 1
        # print(f"--- Tick {self.tick} ---") # Optional console log

        # --- Clear Per-Tick Tracking Lists ---
        self.executed_trade_details_this_tick.clear()
        self.potential_trades_this_tick.clear()
        self.failed_trades_this_tick.clear()
        self.migration_details_this_tick.clear()
        # Note: Settlement production_this_tick is cleared within Settlement.produce()

        # --- Get Current State ---
        current_settlements = list(self.settlements.values())
        active_settlements = [s for s in current_settlements if not s.is_abandoned]

        # --- Core Economic Phases ---
        # 1. Production (includes clearing production_this_tick)
        for settlement in active_settlements:
            settlement.produce(self.goods, self.params, self.tick)
        # 2. Consumption
        for settlement in active_settlements:
            settlement.consume(self.goods, self.params, self.tick)
        # 3. Price Update
        for settlement in active_settlements:
            settlement.update_prices(self.goods, self.params, self.tick)

        # --- Trade Phase ---
        # 4. Find Opportunities
        opportunities = self.find_trade_opportunities()
        # 5. Execute Trades
        self.execute_trades(opportunities)

        # --- Upkeep Phase ---
        # 6. Storage Upkeep
        storage_cost_rate = self.params.get('storage_cost_per_unit', 0.0)
        if storage_cost_rate > 0:
            for settlement in active_settlements:
                total_stored = settlement.get_current_storage_load()
                storage_upkeep = total_stored * storage_cost_rate
                if storage_upkeep > 0: settlement.wealth -= storage_upkeep

        # --- Abandonment Check Phase ---
        # 7. Check for and process settlement abandonment
        settlements_to_remove_ids = []
        abandonment_wealth_threshold = self.params.get('abandonment_wealth_threshold', -100)
        abandonment_ticks_threshold = self.params.get('abandonment_ticks_threshold', 15)

        for settlement in current_settlements: # Iterate original list
            if settlement.is_abandoned: continue
            if settlement.wealth < abandonment_wealth_threshold:
                settlement.ticks_below_wealth_threshold += 1
            else: settlement.ticks_below_wealth_threshold = 0

            if settlement.ticks_below_wealth_threshold >= abandonment_ticks_threshold:
                settlement.is_abandoned = True
                settlements_to_remove_ids.append(settlement.id)
                print(f"INFO: Settlement {settlement.name} ({settlement.id}) abandoned at tick {self.tick} due to prolonged low wealth ({settlement.wealth:.0f}).")
                self.recent_trades_log.insert(0, f"T{self.tick}: {settlement.name} abandoned!")
                self.recent_trades_log = self.recent_trades_log[:10]

        if settlements_to_remove_ids: # Remove after iteration
            print(f"  Removing {len(settlements_to_remove_ids)} abandoned settlements: {settlements_to_remove_ids}")
            for settlement_id in settlements_to_remove_ids:
                if settlement_id in self.settlements: del self.settlements[settlement_id]

        # --- Migration Phase ---
        # 8. Handle population migration between settlements
        migration_interval = self.params.get('migration_check_interval', 5)
        if self.tick % migration_interval == 0 and len(self.settlements) > 1:
            migration_wealth_threshold = self.params.get('migration_wealth_threshold', 0)
            migration_target_min_wealth = self.params.get('migration_target_min_wealth', 600)
            migration_max_percentage = self.params.get('migration_max_percentage', 0.1)

            # Use current active settlements post-abandonment
            current_active_settlements = list(self.settlements.values())
            potential_emigrants = [s for s in current_active_settlements if s.wealth < migration_wealth_threshold and s.population > 1]
            potential_immigrants = [s for s in current_active_settlements if s.wealth >= migration_target_min_wealth]

            if potential_emigrants and potential_immigrants:
                migrants_moved_total = 0
                for emigrant in potential_emigrants:
                    if emigrant.population <= 1: continue
                    if emigrant.id not in self.settlements: continue # Safety check

                    best_target = None; min_dist = float('inf')
                    for immigrant in potential_immigrants:
                        if emigrant.id == immigrant.id: continue
                        if immigrant.id not in self.settlements: continue # Safety check
                        dist = self._calculate_distance(emigrant, immigrant)
                        if dist < min_dist: min_dist = dist; best_target = immigrant

                    if best_target:
                        num_to_migrate = max(1, int(emigrant.population * migration_max_percentage))
                        num_to_migrate = min(num_to_migrate, emigrant.population - 1)

                        if num_to_migrate > 0:
                            emigrant.population -= num_to_migrate
                            best_target.population += num_to_migrate
                            self.migration_details_this_tick.append({
                                'tick': self.tick, 'from_id': emigrant.id, 'from_name': emigrant.name,
                                'to_id': best_target.id, 'to_name': best_target.name, 'quantity': num_to_migrate
                            })
                            emigrant.update_derived_stats()
                            best_target.update_derived_stats()
                            migrants_moved_total += num_to_migrate
                # Optional: print total migrants moved


# --- NO Main Execution Block Here ---
# This file is intended to be imported as a module.
