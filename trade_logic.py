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
# - Data Structures (Good, ItemInstance) : Line 18
# - Settlement Class                      : Line 40
#   - __init__                            : Line 43
#   - update_derived_stats                : Line 66
#   - Storage Management (add/remove/get) : Line 85
#   - produce                             : Line 131
#   - consume                             : Line 182
#   - update_prices                       : Line 198
# - Region Class                          : Line 212
# - Civilization Class                    : Line 216
# - World Class                           : Line 220
#   - __init__                            : Line 221
#   - Entity Management (add/get)         : Line 228
#   - find_trade_opportunities            : Line 234
#   - execute_trades                      : Line 264
#   - _calculate_distance                 : Line 330
#   - simulation_step                     : Line 335
#     - Core Economic Phases              : Line 342
#     - Trade Phase                       : Line 354
#     - Upkeep Phase                      : Line 364
#     - Abandonment Check Phase           : Line 373
#     - Migration Phase                   : Line 399
# ==============================================================================


# ==============================================================================
# Data Structures
# ==============================================================================
class Good:
    """Represents a type of good that can be produced, traded, and consumed."""
    def __init__(self, id, name, base_value, is_bulk=True, is_producible=False):
        """Initializes a Good."""
        self.id = id
        self.name = name
        self.base_value = base_value
        self.is_bulk = is_bulk  # Bulk goods stack, non-bulk are distinct items
        self.is_producible = is_producible # Can this good be made via a recipe?
        self.recipe = None # Stores production recipe if is_producible

    def __repr__(self):
        """String representation of the Good."""
        return f"Good({self.name})"

    def add_recipe(self, inputs, outputs, labor, required_terrain=None, wealth_cost=0):
        """Adds a production recipe to a producible good."""
        if not self.is_producible:
            print(f"WARN: Cannot add recipe to non-producible good: {self.name}")
            return
        # Input validation
        if not isinstance(inputs, dict): raise TypeError(f"Recipe inputs for {self.id} must be a dict")
        if not isinstance(outputs, dict): raise TypeError(f"Recipe outputs for {self.id} must be a dict")
        if not outputs: raise ValueError(f"Recipe for {self.id} must have outputs")

        self.recipe = {
            'inputs': inputs,           # Dict[good_id, quantity]
            'outputs': outputs,         # Dict[good_id, quantity]
            'labor': float(labor),      # Labor units required
            'required_terrain': required_terrain, # Optional list of terrain types
            'wealth_cost': float(wealth_cost) # Direct wealth cost for production
        }

class ItemInstance:
    """Represents a specific instance of a non-bulk good, tracking its history."""
    def __init__(self, good_id, origin_settlement_id, quantity=1, quality=1.0):
        """Initializes an ItemInstance."""
        self.instance_id = str(uuid.uuid4()) # Unique ID for this specific item
        self.good_id = good_id               # Type of good this instance is
        self.origin_settlement_id = origin_settlement_id # Where it was first created
        self.current_location_settlement_id = origin_settlement_id # Where it is now
        self.quantity = quantity             # Amount (relevant if non-bulk can have quantity > 1, e.g., a bundle)
        self.quality = quality               # Potential future use for quality levels
        self.trade_history = []              # List of (settlement_id, price, tick) tuples

    def __repr__(self):
        """String representation of the ItemInstance."""
        history_summary = f", History: {len(self.trade_history)} steps" if self.trade_history else ""
        return (f"Item(ID: {self.instance_id[:4]}..., Good: {self.good_id}, "
                f"Origin: {self.origin_settlement_id}, Loc: {self.current_location_settlement_id}, "
                f"Qty: {self.quantity:.1f}{history_summary})")

# ==============================================================================
# Settlement Class
# ==============================================================================
class Settlement:
    """Represents a settlement, the core economic unit, managing population,
       storage, production, consumption, and local prices."""

    def __init__(self, id, name, region_id, population, terrain_type,
                 storage_capacity_per_pop, labor_per_pop, default_initial_wealth,
                 city_population_threshold, city_storage_multiplier, # Base params
                 initial_wealth=None, x=0, y=0, z=0): # <<< Added z coordinate
        """Initializes a Settlement."""
        self.id = id
        self.name = name
        self.region_id = region_id
        self.population = max(1, population) # Ensure population is at least 1
        self.terrain_type = terrain_type
        self.x = x
        self.y = y
        self.z = z # <<< Storing the z coordinate

        # Storage: Separate dicts for bulk goods (float quantity) and item instances (list of ItemInstance)
        self.bulk_storage = defaultdict(float)
        self.item_storage = defaultdict(list)

        # Economic state
        self.consumption_needs = defaultdict(lambda: 1.0) # Modifier for demand
        self.local_prices = {} # Calculated prices for goods {good_id: price}
        self.wealth = initial_wealth if initial_wealth is not None else default_initial_wealth
        self.market_level = 1 # Potential future use for market size/efficiency
        self.log = [] # Short log of recent events for this settlement

        # Store base parameters needed for dynamic calculation based on population
        self._storage_capacity_per_pop = storage_capacity_per_pop
        self._labor_per_pop = labor_per_pop
        self._city_pop_threshold = city_population_threshold
        self._city_storage_multiplier = city_storage_multiplier

        # Initial calculation of derived stats (updated by update_derived_stats)
        self.max_labor_pool = 0
        self.storage_capacity = 0
        self.current_labor_pool = 0
        self.update_derived_stats() # Calculate initial values based on starting pop

        # State for Abandonment tracking
        self.ticks_below_wealth_threshold = 0
        self.is_abandoned = False # Flag to mark for removal by World

        # FUTURE: Refactor Settlement to act as a container/manager for internal Building and Agent objects.
        # FUTURE: Replace 'population' int with a collection of Agent objects, each with specialized roles/state.
        # FUTURE: Decide if wealth/storage remains central (Town Hall) or becomes distributed among internal Agents/Buildings.
        # FUTURE: Internal buildings/agents might need relative coordinates within the settlement area.

    def update_derived_stats(self):
        """Recalculates stats based on current population (e.g., after migration)."""
        self.population = max(1, self.population) # Ensure pop doesn't drop below 1

        # Calculate max labor pool based on population
        self.max_labor_pool = self.population * self._labor_per_pop
        # Replenish labor pool when stats update (represents new labor becoming available)
        self.current_labor_pool = self.max_labor_pool

        # Recalculate storage capacity based on population and city status
        base_capacity = self.population * self._storage_capacity_per_pop
        if self.population >= self._city_pop_threshold:
            self.storage_capacity = base_capacity * self._city_storage_multiplier
        else:
            self.storage_capacity = base_capacity

    def __repr__(self):
        """String representation of the Settlement."""
        # <<< Updated to include Z coordinate >>>
        return (f"Settlement({self.name}, Pop: {self.population}, "
                f"Wealth: {self.wealth:.0f}, Terrain: {self.terrain_type}, "
                f"Pos:({self.x},{self.y},{self.z}))")

    def add_log(self, message, tick):
        """Adds a message to the settlement's event log."""
        self.log.append(f"T{tick}: {message}")
        self.log = self.log[-10:] # Keep only the last 10 messages

    # --- Storage Management ---
    def get_total_stored(self, good_id):
        """Returns the total quantity of a specific good in storage (bulk + items)."""
        bulk_qty = self.bulk_storage.get(good_id, 0)
        item_qty = sum(item.quantity for item in self.item_storage.get(good_id, []))
        return bulk_qty + item_qty

    def get_current_storage_load(self):
        """Returns the total quantity of all goods currently stored."""
        total_bulk = sum(self.bulk_storage.values())
        total_items = sum(item.quantity for items in self.item_storage.values() for item in items)
        return total_bulk + total_items

    def add_to_storage(self, good, quantity=None, item_instance=None, tick=0):
        """Adds goods to storage, respecting capacity. Returns quantity added."""
        current_load = self.get_current_storage_load()
        available_capacity = max(0, self.storage_capacity - current_load)
        added_qty = 0

        if available_capacity <= 1e-6: # Check if storage is effectively full
            # self.add_log(f"Storage full, cannot add {good.id if good else item_instance.good_id}", tick)
            return 0 # Cannot add anything

        if item_instance: # Adding a specific non-bulk item instance
            needed_capacity = item_instance.quantity
            if needed_capacity <= available_capacity:
                self.item_storage[item_instance.good_id].append(item_instance)
                item_instance.current_location_settlement_id = self.id # Update item location
                added_qty = item_instance.quantity
            else:
                # Not enough space for the whole item instance (should ideally not happen with current trade logic)
                # self.add_log(f"Not enough space for item {item_instance.good_id}", tick)
                pass # Don't add partial instances for now
        elif good and quantity is not None: # Adding a quantity of a good (likely bulk)
            amount_to_add = min(quantity, available_capacity)
            if amount_to_add > 1e-6: # Only add if it's a meaningful amount
                if good.is_bulk:
                    self.bulk_storage[good.id] += amount_to_add
                else:
                    # Create a new instance if adding non-bulk goods this way (e.g., initial setup)
                    new_instance = ItemInstance(good.id, self.id, quantity=amount_to_add)
                    self.item_storage[good.id].append(new_instance)
                added_qty = amount_to_add

        # if added_qty < (quantity if quantity is not None else (item_instance.quantity if item_instance else 0)) * 0.99:
        #     self.add_log(f"Added only {added_qty:.1f} due to space limit", tick)

        return added_qty

    def remove_from_storage(self, good_id, quantity, tick=0):
        """Removes goods from storage. Returns (quantity_removed, list_of_consumed_item_instances)."""
        removed_qty = 0
        consumed_instances = [] # Stores parts of ItemInstances consumed

        # 1. Remove from bulk storage first
        if good_id in self.bulk_storage:
            take_from_bulk = min(quantity, self.bulk_storage[good_id])
            self.bulk_storage[good_id] -= take_from_bulk
            removed_qty += take_from_bulk
            if self.bulk_storage[good_id] < 1e-6: # Clean up if storage is empty
                del self.bulk_storage[good_id]

        # 2. Remove remaining needed quantity from item storage
        remaining_needed = quantity - removed_qty
        if remaining_needed > 1e-6 and good_id in self.item_storage:
            items_list = self.item_storage[good_id]
            indices_to_remove = [] # Track indices of fully consumed items

            # Iterate through item instances of this good
            for i, item in enumerate(items_list):
                if remaining_needed <= 1e-6: break # Stop if requirement met

                take_from_item = min(remaining_needed, item.quantity)

                # Create a representation of the consumed part (for trade/consumption tracking)
                # This copies relevant data from the original item instance
                consumed_instance_part = ItemInstance(
                    good_id=item.good_id,
                    origin_settlement_id=item.origin_settlement_id,
                    quantity=take_from_item,
                    quality=item.quality
                )
                consumed_instance_part.instance_id = item.instance_id # Keep original instance ID
                consumed_instance_part.trade_history = item.trade_history[:] # Copy history
                consumed_instances.append(consumed_instance_part)

                # Update the original item instance
                item.quantity -= take_from_item
                removed_qty += take_from_item
                remaining_needed -= take_from_item

                # Mark item for removal if fully consumed
                if item.quantity < 1e-6:
                    indices_to_remove.append(i)

            # Remove fully consumed items from storage (in reverse order to avoid index issues)
            for i in sorted(indices_to_remove, reverse=True):
                del items_list[i]

            # Clean up the item storage dict if the list becomes empty
            if not self.item_storage[good_id]:
                del self.item_storage[good_id]

        # if removed_qty < quantity * 0.99:
        #     self.add_log(f"Could only remove {removed_qty:.1f}/{quantity:.1f} of {good_id}", tick)

        return removed_qty, consumed_instances

    # --- Economic Actions ---
    def produce(self, all_goods_dict, params, world_tick):
        """Attempts to produce goods based on available recipes, labor, resources, and wealth."""
        # FUTURE: Delegate production logic to specific internal Agent/Building objects.

        # Get parameters from world config
        max_production_passes = params.get('max_production_passes', 5)
        production_wealth_buffer = params.get('production_wealth_buffer', 0.0)

        # --- Production Halt Check ---
        # Stop production if wealth is below the configured buffer
        if self.wealth < production_wealth_buffer:
            # Optional log: print(f"DEBUG: {self.name} halting production, wealth {self.wealth:.0f} < buffer {production_wealth_buffer:.0f}")
            return # Don't produce if below buffer

        # Replenish labor pool at the start of the production phase for this tick
        self.current_labor_pool = self.max_labor_pool

        # --- Production Loop ---
        # Multiple passes allow dependent productions (e.g., ore -> tools) in the same tick
        for _pass in range(max_production_passes):
            production_possible_in_pass = False # Flag to check if any production happened

            # Get list of goods that can be produced (have recipes)
            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            if not producible_goods: break # No producible goods defined

            # Shuffle the order to avoid bias towards goods defined earlier
            producible_items = list(producible_goods.items())
            random.shuffle(producible_items)

            # Try producing each item
            for good_id, good in producible_items:
                recipe = good.recipe

                # --- Check Production Feasibility ---
                # 1. Terrain requirement
                if recipe['required_terrain'] and self.terrain_type not in recipe['required_terrain']:
                    continue
                # 2. Labor requirement
                if self.current_labor_pool < recipe['labor']:
                    continue
                # 3. Direct wealth cost requirement
                if self.wealth < recipe['wealth_cost']:
                    continue
                # 4. Input goods requirement
                inputs_available = True
                required_inputs = recipe['inputs']
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        if self.get_total_stored(input_good_id) < input_qty:
                            inputs_available = False
                            break
                    if not inputs_available:
                        continue # Missing required input goods

                # --- Attempt Production ---
                # Store current state in case we need to revert
                original_labor = self.current_labor_pool
                original_wealth = self.wealth
                temp_input_storage_state = {} # Store initial quantities of inputs
                temp_output_storage_state = {} # Store initial quantities of outputs

                # 1. Consume Labor & Wealth Cost
                self.current_labor_pool -= recipe['labor']
                self.wealth -= recipe['wealth_cost']

                # 2. Consume Inputs
                inputs_consumed_successfully = True
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        temp_input_storage_state[input_good_id] = self.get_total_stored(input_good_id)
                        removed_qty, _ = self.remove_from_storage(input_good_id, input_qty, tick=world_tick)
                        # Check if enough was actually removed (allowing for small float errors)
                        if removed_qty < input_qty * 0.999:
                            inputs_consumed_successfully = False
                            # Revert state
                            self.current_labor_pool = original_labor
                            self.wealth = original_wealth
                            # Add back any partially removed inputs
                            for gid, initial_qty in temp_input_storage_state.items():
                                 current_qty = self.get_total_stored(gid)
                                 qty_to_add_back = initial_qty - current_qty
                                 if qty_to_add_back > 1e-6:
                                     self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                            break # Stop trying to consume inputs for this recipe
                    if not inputs_consumed_successfully:
                        continue # Move to the next recipe

                # 3. Add Outputs
                outputs_produced_successfully = True
                for output_good_id, output_qty in recipe['outputs'].items():
                    output_good = all_goods_dict[output_good_id]
                    temp_output_storage_state[output_good_id] = self.get_total_stored(output_good_id)
                    added_qty = self.add_to_storage(output_good, quantity=output_qty, tick=world_tick)
                    # Check if enough was actually added (respecting storage limits)
                    if added_qty < output_qty * 0.999:
                        outputs_produced_successfully = False
                        # Revert state: Labor, Wealth, Inputs, and partially added Outputs
                        self.current_labor_pool = original_labor
                        self.wealth = original_wealth
                        # Add back consumed inputs
                        for gid, initial_qty in temp_input_storage_state.items():
                             current_qty = self.get_total_stored(gid)
                             qty_to_add_back = initial_qty - current_qty
                             if qty_to_add_back > 1e-6:
                                 self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                        # Remove partially added outputs
                        for gid, initial_qty in temp_output_storage_state.items():
                            current_qty = self.get_total_stored(gid)
                            qty_to_remove = current_qty - initial_qty
                            if qty_to_remove > 1e-6:
                                self.remove_from_storage(gid, qty_to_remove)
                        # self.add_log(f"Production failed for {good_id} (output storage full?)", world_tick)
                        break # Stop trying to add outputs for this recipe
                if not outputs_produced_successfully:
                    continue # Move to the next recipe

                # If we reach here, production was successful for this recipe instance
                # self.add_log(f"Produced {recipe['outputs']}", world_tick)
                production_possible_in_pass = True # Mark that production occurred in this pass

            # If no production was possible in this entire pass, stop iterating
            if not production_possible_in_pass:
                break

    def consume(self, goods_dict, params, world_tick):
        """Consumes goods based on population and needs."""
        # FUTURE: Delegate consumption logic to internal Agent/Building objects.

        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            # Basic logic: skip raw materials, cities consume bread instead of grain
            if good_id in ['iron_ore', 'seed']: continue # Don't consume raw ore/seed directly

            consume_this = False
            if good_id == 'bread' and is_city: consume_this = True # Cities need bread
            elif good_id != 'bread' and not (good_id == 'grain' and is_city): consume_this = True # Non-cities consume grain, everyone consumes other non-bread goods

            if consume_this:
                # Calculate base need based on population and consumption rate
                demand_modifier = self.consumption_needs[good_id] # Apply specific need modifier
                amount_needed = (base_consumption_rate * self.population * demand_modifier
                                 * (1 + random.uniform(-0.1, 0.1))) # Add small random fluctuation
                amount_needed = max(0, amount_needed) # Ensure non-negative

                if amount_needed > 0.01: # Only consume if need is significant
                    available = self.get_total_stored(good_id)
                    amount_to_consume = min(amount_needed, available)

                    if amount_to_consume > 0.01: # Only consume if available amount is significant
                        removed_qty, _ = self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)
                        # Optional: Add consumption log or track unmet needs
                        # if removed_qty < amount_needed * 0.9:
                        #     self.add_log(f"Shortage! Needed {amount_needed:.1f} {good_id}, consumed {removed_qty:.1f}", world_tick)

    def update_prices(self, goods_dict, params, world_tick):
        """Updates local prices based on supply and demand estimates."""
        # FUTURE: Delegate price setting to a central 'Market' building/entity.

        # Get parameters
        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        price_sensitivity = params.get('price_sensitivity', 2.0) # How much prices react to supply/demand ratio
        min_price_multiplier = params.get('min_price_multiplier', 0.1) # Min price relative to base
        max_price_multiplier = params.get('max_price_multiplier', 10.0) # Max price relative to base
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            # Estimate supply (current stock)
            supply = self.get_total_stored(good_id)
            supply = max(supply, 0.01) # Avoid division by zero, assume minimal supply if empty

            # Estimate demand (based on consumption logic)
            demand_estimate = 0.01 # Assume minimal demand baseline
            if good_id not in ['iron_ore', 'seed']: # No direct consumption demand for these
                 if good_id == 'bread' and is_city:
                     demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
                 elif good_id != 'bread' and not (good_id == 'grain' and is_city):
                     demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
            demand_estimate = max(demand_estimate, 0.01) # Avoid division by zero

            # Calculate supply/demand ratio
            ratio = supply / demand_estimate

            # Calculate price modifier based on ratio and sensitivity
            # ratio > 1 (supply > demand) -> modifier < 1 -> lower price
            # ratio < 1 (supply < demand) -> modifier > 1 -> higher price
            price_modifier = math.pow(ratio, -price_sensitivity)

            # Calculate price bounds
            min_price = good.base_value * min_price_multiplier
            max_price = good.base_value * max_price_multiplier

            # Calculate final price and clamp within bounds
            new_price = good.base_value * price_modifier
            self.local_prices[good_id] = max(min_price, min(new_price, max_price))

# ==============================================================================
# Region Class
# ==============================================================================
class Region:
    """Represents a geographical region containing settlements."""
    def __init__(self, id, name, resource_modifiers=None):
        """Initializes a Region."""
        self.id = id
        self.name = name
        self.resource_modifiers = resource_modifiers if resource_modifiers else {} # Potential future use
        self.settlements = [] # List of settlements in this region

    def add_settlement(self, settlement):
        """Adds a settlement to the region."""
        self.settlements.append(settlement)

# ==============================================================================
# Civilization Class
# ==============================================================================
class Civilization:
    """Represents a civilization encompassing multiple regions."""
    def __init__(self, id, name):
        """Initializes a Civilization."""
        self.id = id
        self.name = name
        self.regions = [] # List of regions belonging to this civilization

    def add_region(self, region):
        """Adds a region to the civilization."""
        self.regions.append(region)

# ==============================================================================
# World Class
# ==============================================================================
class World:
    """Manages the overall simulation state, including time, entities,
       and the main simulation loop."""

    def __init__(self, sim_params):
        """Initializes the World."""
        self.tick = 0 # Simulation time counter
        self.goods = OrderedDict() # {good_id: Good object}
        self.settlements = OrderedDict() # {settlement_id: Settlement object}
        self.regions = OrderedDict() # {region_id: Region object}
        self.civilizations = OrderedDict() # {civ_id: Civilization object}
        self.trade_routes = {} # Potential future use for established routes

        # Logging and tracking for UI/analysis
        self.recent_trades_log = [] # Stores strings describing recent executed trades
        self.executed_trade_details_this_tick = [] # Detailed dicts of successful trades
        self.potential_trades_this_tick = [] # Detailed dicts of potential trades found
        self.failed_trades_this_tick = [] # Detailed dicts of trades that failed execution
        self.migration_details_this_tick = [] # <<< List to store migration events this tick

        self.params = sim_params # Dictionary of simulation parameters from config
        print(f"World initialized with parameters: {self.params}")

    # --- Entity Management ---
    def add_good(self, good):
        """Adds a Good to the world."""
        self.goods[good.id] = good

    def add_settlement(self, settlement):
        """Adds a Settlement to the world."""
        self.settlements[settlement.id] = settlement

    def add_region(self, region):
        """Adds a Region to the world."""
        self.regions[region.id] = region

    def add_civilization(self, civilization):
        """Adds a Civilization to the world."""
        self.civilizations[civilization.id] = civilization

    def get_all_settlements(self):
        """Returns a list of all current Settlement objects."""
        return list(self.settlements.values())

    # --- Trade Logic ---
    def find_trade_opportunities(self):
        """Identifies potential trade opportunities between settlements based on price differences."""
        self.potential_trades_this_tick.clear() # Clear previous tick's data
        opportunities_for_execution = [] # List of trades viable enough to attempt execution

        all_settlements = self.get_all_settlements()
        # Ensure we only consider non-abandoned settlements for finding trades
        active_settlements = [s for s in all_settlements if not s.is_abandoned]

        price_threshold_multiplier = self.params.get('trade_profit_margin_threshold', 1.05)

        # Compare every pair of active settlements
        for i in range(len(active_settlements)):
            for j in range(i + 1, len(active_settlements)):
                settlement_a = active_settlements[i]
                settlement_b = active_settlements[j]

                # Check potential trades for every good type
                for good_id, good in self.goods.items():
                    price_a = settlement_a.local_prices.get(good_id)
                    price_b = settlement_b.local_prices.get(good_id)

                    # Skip if either settlement doesn't have a price for this good
                    if price_a is None or price_b is None: continue

                    profit, seller, buyer, qty_avail = 0, None, None, 0
                    seller_price, buyer_price = 0, 0

                    # Check if B buying from A is profitable enough
                    if price_b > price_a * price_threshold_multiplier:
                        profit = price_b - price_a
                        seller, buyer = settlement_a, settlement_b
                        seller_price, buyer_price = price_a, price_b
                        qty_avail = seller.get_total_stored(good_id)
                    # Check if A buying from B is profitable enough
                    elif price_a > price_b * price_threshold_multiplier:
                        profit = price_a - price_b
                        seller, buyer = settlement_b, settlement_a
                        seller_price, buyer_price = price_b, price_a
                        qty_avail = seller.get_total_stored(good_id)

                    # If a profitable trade direction was found
                    if seller is not None:
                        # Estimate potential quantity (this will be refined during execution)
                        potential_trade_qty = 0
                        if qty_avail > 1e-6:
                             # For bulk goods, assume a base potential of 1 (will be scaled later)
                             # For non-bulk, potential is limited by the smallest instance quantity
                             potential_trade_qty = 1.0 # Default for bulk
                             if not good.is_bulk and good_id in seller.item_storage:
                                 items = seller.item_storage[good_id]
                                 # If items exist, potential is the quantity of the first one
                                 # (assumes trading whole non-bulk items)
                                 potential_trade_qty = items[0].quantity if items else 0
                             # Ensure potential qty doesn't exceed available stock
                             potential_trade_qty = min(potential_trade_qty, qty_avail)
                             if potential_trade_qty < 1e-6: potential_trade_qty = 0 # Ignore tiny amounts

                        # Preliminary viability check (basic checks before adding to execution list)
                        is_viable_prelim = (profit > 1e-6 and
                                           potential_trade_qty > 1e-6 and
                                           buyer.wealth > 0 and # Buyer needs some wealth
                                           seller.wealth >= 0) # Seller shouldn't be in extreme debt (optional check)

                        # Log all potential opportunities found for analysis
                        self.potential_trades_this_tick.append({
                            'seller_id': seller.id, 'buyer_id': buyer.id,
                            'seller_name': seller.name, 'buyer_name': buyer.name,
                            'good_id': good.id, 'good_name': good.name,
                            'seller_price': seller_price, 'buyer_price': buyer_price,
                            'profit_per_unit': profit, 'qty_avail': qty_avail,
                            'potential_qty': potential_trade_qty,
                            'is_viable_prelim': is_viable_prelim
                        })

                        # If preliminarily viable, add to the list for attempted execution
                        if is_viable_prelim:
                            opportunities_for_execution.append({
                                'from': seller, 'to': buyer, 'good': good,
                                'profit_per_unit': profit,
                                'potential_qty': potential_trade_qty, # Base potential qty
                                'seller_price': seller_price,
                                'buyer_price': buyer_price
                            })

        # Sort opportunities by profit per unit (descending) to prioritize most profitable trades
        opportunities_for_execution.sort(key=lambda x: x['profit_per_unit'], reverse=True)
        return opportunities_for_execution

    def execute_trades(self, opportunities):
        """Attempts to execute the identified trade opportunities, respecting limits and constraints."""
        trades_executed_log_entries = [] # For the simple UI log
        self.executed_trade_details_this_tick.clear() # Clear previous tick's data
        self.failed_trades_this_tick.clear() # Clear previous tick's data

        trades_count = 0
        max_trades = self.params.get('max_trades_per_tick', 200) # Global limit

        # Process opportunities (sorted by profit)
        for i, trade in enumerate(opportunities):
            fail_reason = "" # Store reason if trade fails
            seller = trade['from']
            buyer = trade['to']
            good = trade['good']
            profit = trade['profit_per_unit']
            potential_qty = trade['potential_qty'] # Base potential from find_trade_opportunities
            seller_price = trade['seller_price']

            # Base info for logging failures
            fail_log_base = {
                'seller_id': seller.id, 'buyer_id': buyer.id,
                'seller_name': seller.name, 'buyer_name': buyer.name,
                'good_id': good.id, 'good_name': good.name,
                'seller_price': seller_price, 'buyer_price': trade['buyer_price'],
                'profit_per_unit': profit, 'potential_qty': potential_qty,
                'qty_avail': seller.get_total_stored(good.id) # Current available qty at execution time
            }

            # Check global trade limit
            if trades_count >= max_trades:
                fail_reason = "Skipped (Max Trades Reached)"
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                continue # Stop processing trades if limit reached

            # --- Determine Actual Trade Quantity ---
            # (This is where bulk trade logic will be implemented in Phase 1)
            trade_qty = 0
            item_to_trade_instance_id = None # Track specific item ID for non-bulk

            if good.is_bulk:
                 # TODO PHASE 1: Implement bulk trade quantity calculation here
                 # Based on potential_qty, buyer wealth, buyer storage, seller stock
                 trade_qty = min(potential_qty, 1.0) # Placeholder - capped at 1.0 for now
            else: # Non-bulk goods - trade the specific instance found earlier
                 if good.id in seller.item_storage and seller.item_storage[good.id]:
                    # Assume trading the first available instance
                    item_to_trade = seller.item_storage[good.id][0]
                    trade_qty = item_to_trade.quantity
                    item_to_trade_instance_id = item_to_trade.instance_id
                 else:
                    # Item might have been consumed/traded between find and execute
                    fail_reason = "Seller Lacks Non-Bulk Item (at execution)"
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                    continue # Skip to next trade opportunity

            # Ensure trade quantity is meaningful
            trade_qty = max(0.01, trade_qty) # Set minimum trade size
            if trade_qty < 0.01:
                 fail_reason = f"Trade quantity too small ({trade_qty:.3f})"
                 self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason})
                 continue

            # --- Check Execution Feasibility ---
            transaction_price = seller_price # Price per unit
            transaction_cost = transaction_price * trade_qty # Total cost for the buyer

            # Check buyer affordability and seller stock *at the time of execution*
            can_afford = buyer.wealth >= transaction_cost
            has_stock = seller.get_total_stored(good.id) >= trade_qty

            if not can_afford: fail_reason += f"Buyer Cannot Afford ({buyer.wealth:.0f} < {transaction_cost:.0f}); "
            if not has_stock: fail_reason += f"Seller Lacks Stock ({seller.get_total_stored(good.id):.1f} < {trade_qty:.1f}); "

            # --- Execute Transaction ---
            if can_afford and has_stock:
                # 1. Remove from seller's storage
                removed_qty, consumed_instances = seller.remove_from_storage(good.id, trade_qty, tick=self.tick)

                # Check if removal was successful (should match trade_qty closely)
                if removed_qty < trade_qty * 0.99:
                    fail_reason += f"Failed Stock Removal ({removed_qty:.1f}/{trade_qty:.1f})"
                    # Attempt to add back partially removed stock (best effort)
                    if consumed_instances: # For non-bulk
                         seller.add_to_storage(good, item_instance=consumed_instances[0], tick=self.tick)
                    elif removed_qty > 1e-6: # For bulk
                         seller.add_to_storage(good, quantity=removed_qty, tick=self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})
                    continue # Skip to next trade

                # Prepare item instance for buyer if non-bulk
                item_instance_for_buyer = None
                if not good.is_bulk and consumed_instances:
                    original_instance_part = consumed_instances[0]
                    # Create a new instance for the buyer based on the consumed part
                    item_instance_for_buyer = ItemInstance(
                        good_id=good.id,
                        origin_settlement_id=original_instance_part.origin_settlement_id,
                        quantity=removed_qty, # Use actual removed quantity
                        quality=original_instance_part.quality
                    )
                    # Copy trade history and add this trade
                    item_instance_for_buyer.trade_history = original_instance_part.trade_history[:]
                    item_instance_for_buyer.trade_history.append((seller.id, transaction_price, self.tick))
                    # Keep the original instance ID if possible (helps tracking)
                    if item_to_trade_instance_id:
                        item_instance_for_buyer.instance_id = item_to_trade_instance_id

                # 2. Add to buyer's storage
                added_qty = buyer.add_to_storage(
                    good,
                    quantity=removed_qty if good.is_bulk else None, # Pass quantity only for bulk
                    item_instance=item_instance_for_buyer, # Pass instance for non-bulk
                    tick=self.tick
                )

                # 3. Check if addition was successful (respecting buyer's storage capacity)
                if added_qty >= removed_qty * 0.99:
                    # Success! Finalize wealth transfer
                    final_cost = transaction_price * added_qty # Use actual added quantity for cost
                    seller.wealth += final_cost
                    buyer.wealth -= final_cost

                    # Log successful trade
                    trade_log_msg = (f"T{self.tick}: {seller.name} -> {buyer.name}, "
                                     f"{added_qty:.2f} {good.name} @ {transaction_price:.2f}")
                    trades_executed_log_entries.append(trade_log_msg)
                    self.executed_trade_details_this_tick.append({
                        'seller_id': seller.id, 'buyer_id': buyer.id,
                        'seller_name': seller.name, 'buyer_name': buyer.name,
                        'good_id': good.id, 'good_name': good.name,
                        'quantity': added_qty, 'seller_price': seller_price,
                        'buyer_price': trade['buyer_price'], 'profit_per_unit': profit,
                        'tick': self.tick
                    })
                    trades_count += 1 # Increment successful trade counter
                else:
                    # Failed to add to buyer's storage (likely full)
                    fail_reason += f"Buyer Storage Failed (Avail: {max(0, buyer.storage_capacity - buyer.get_current_storage_load()):.1f})"
                    # Return the goods to the seller
                    item_to_return = None
                    if not good.is_bulk and consumed_instances:
                        item_to_return = consumed_instances[0]
                        # Remove the failed trade from the item's history
                        if item_to_return.trade_history: item_to_return.trade_history.pop()

                    seller.add_to_storage(
                        good,
                        quantity=removed_qty if good.is_bulk else None,
                        item_instance=item_to_return,
                        tick=self.tick
                    )
                    # Log failure
                    seller.add_log(f"Fail trade to {buyer.name} (storage?), {removed_qty:.1f} {good.name} returned", self.tick)
                    buyer.add_log(f"Fail trade from {seller.name} (storage full?)", self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})
            else:
                # Failed initial check (affordability or stock)
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})

        # Update the main trade log displayed in the UI
        self.recent_trades_log = trades_executed_log_entries + self.recent_trades_log
        self.recent_trades_log = self.recent_trades_log[:10] # Keep last 10 entries

    # --- Utility Methods ---
    def _calculate_distance(self, s1, s2):
        """Calculate Euclidean distance between two settlements in 3D space."""
        # <<< Updated for 3D coordinates >>>
        return math.sqrt((s1.x - s2.x)**2 + (s1.y - s2.y)**2 + (s1.z - s2.z)**2)

    # ==========================================================================
    # Main Simulation Step
    # ==========================================================================
    def simulation_step(self):
        """Executes one full tick of the simulation including production,
           consumption, trade, upkeep, abandonment, and migration."""
        # FUTURE: Add simulation phases for Agent actions (pathfinding, task execution) and Building management.

        self.tick += 1
        print(f"--- Tick {self.tick} ---") # Basic console progress indicator

        # Clear per-tick tracking lists
        self.executed_trade_details_this_tick.clear()
        self.potential_trades_this_tick.clear()
        self.failed_trades_this_tick.clear()
        self.migration_details_this_tick.clear() # <<< Clear migration details

        # Use list(self.settlements.values()) for iteration in case settlements dict changes during loop (e.g., abandonment)
        current_settlements = list(self.settlements.values())
        active_settlements = [s for s in current_settlements if not s.is_abandoned]

        # --- Core Economic Phases ---
        # 1. Production: Settlements attempt to produce goods
        start_time = time.time()
        for settlement in active_settlements:
            settlement.produce(self.goods, self.params, self.tick)
        # print(f"  Production took: {time.time() - start_time:.4f}s")

        # 2. Consumption: Settlements consume goods based on population needs
        start_time = time.time()
        for settlement in active_settlements:
            settlement.consume(self.goods, self.params, self.tick)
        # print(f"  Consumption took: {time.time() - start_time:.4f}s")

        # 3. Price Update: Settlements adjust local prices based on supply/demand
        start_time = time.time()
        for settlement in active_settlements:
            settlement.update_prices(self.goods, self.params, self.tick)
        # print(f"  Price Update took: {time.time() - start_time:.4f}s")

        # --- Trade Phase ---
        # 4. Find Opportunities: Identify potential profitable trades
        start_time = time.time()
        opportunities = self.find_trade_opportunities()
        # print(f"  Find Trades took: {time.time() - start_time:.4f}s ({len(opportunities)} potential)")

        # 5. Execute Trades: Attempt to execute the found opportunities
        start_time = time.time()
        self.execute_trades(opportunities)
        # print(f"  Execute Trades took: {time.time() - start_time:.4f}s ({len(self.executed_trade_details_this_tick)} executed)")

        # --- Upkeep Phase ---
        # 6. Storage Upkeep: Deduct wealth based on stored goods quantity
        start_time = time.time()
        storage_cost_rate = self.params.get('storage_cost_per_unit', 0.0)
        if storage_cost_rate > 0:
            for settlement in active_settlements:
                total_stored = settlement.get_current_storage_load()
                storage_upkeep = total_stored * storage_cost_rate
                if storage_upkeep > 0:
                    settlement.wealth -= storage_upkeep
                    # Optional: Log upkeep cost
                    # settlement.add_log(f"Paid {storage_upkeep:.1f} upkeep for {total_stored:.1f} units", self.tick)
        # print(f"  Upkeep took: {time.time() - start_time:.4f}s")

        # --- Abandonment Check Phase ---
        # 7. Check for and process settlement abandonment
        start_time = time.time()
        settlements_to_remove_ids = []
        abandonment_wealth_threshold = self.params.get('abandonment_wealth_threshold', -100)
        abandonment_ticks_threshold = self.params.get('abandonment_ticks_threshold', 15)

        # Iterate using the original list in case abandonment happens mid-loop
        for settlement in current_settlements:
            if settlement.is_abandoned: continue # Already marked

            # Check wealth threshold
            if settlement.wealth < abandonment_wealth_threshold:
                settlement.ticks_below_wealth_threshold += 1
            else:
                settlement.ticks_below_wealth_threshold = 0 # Reset counter if wealth recovers

            # Check if threshold duration is met
            if settlement.ticks_below_wealth_threshold >= abandonment_ticks_threshold:
                settlement.is_abandoned = True # Mark for removal
                settlements_to_remove_ids.append(settlement.id)
                print(f"INFO: Settlement {settlement.name} ({settlement.id}) abandoned at tick {self.tick} due to prolonged low wealth ({settlement.wealth:.0f}).")
                # Add abandonment event to the main trade log for visibility
                self.recent_trades_log.insert(0, f"T{self.tick}: {settlement.name} abandoned!")
                self.recent_trades_log = self.recent_trades_log[:10]

        # Remove abandoned settlements from the main dictionary *after* iteration
        if settlements_to_remove_ids:
            print(f"  Removing {len(settlements_to_remove_ids)} abandoned settlements: {settlements_to_remove_ids}")
            for settlement_id in settlements_to_remove_ids:
                if settlement_id in self.settlements:
                    del self.settlements[settlement_id]
            # The list of active settlements for the *next* tick will be updated automatically
        # print(f"  Abandonment took: {time.time() - start_time:.4f}s")


        # --- Migration Phase ---
        # 8. Handle population migration between settlements
        start_time = time.time()
        migration_interval = self.params.get('migration_check_interval', 5)

        # Only run migration periodically and if there's more than one settlement left
        # Use the *current* state of self.settlements after potential abandonment
        if self.tick % migration_interval == 0 and len(self.settlements) > 1:
            # print(f"--- T{self.tick}: Migration Phase ---")
            migration_wealth_threshold = self.params.get('migration_wealth_threshold', 0)
            migration_target_min_wealth = self.params.get('migration_target_min_wealth', 600)
            migration_max_percentage = self.params.get('migration_max_percentage', 0.1)

            # Get current active settlements for migration checks
            current_active_settlements = list(self.settlements.values())

            # Separate potential emigrants and immigrants first
            potential_emigrants = [s for s in current_active_settlements if s.wealth < migration_wealth_threshold and s.population > 1]
            potential_immigrants = [s for s in current_active_settlements if s.wealth >= migration_target_min_wealth]

            if not potential_emigrants or not potential_immigrants:
                # print("  No suitable emigrants or immigration targets found.")
                pass
            else:
                # print(f"  Potential Emigrants: {[s.id for s in potential_emigrants]}")
                # print(f"  Potential Immigrants: {[s.id for s in potential_immigrants]}")

                migrants_moved_total = 0
                # Process each potential emigrant settlement
                for emigrant in potential_emigrants:
                    # Double-check population hasn't dropped to 1 due to previous migrations this tick
                    if emigrant.population <= 1: continue

                    # Find the closest suitable target among potential immigrants
                    best_target = None
                    min_dist = float('inf')
                    for immigrant in potential_immigrants:
                        if emigrant.id == immigrant.id: continue # Don't migrate to self
                        # Ensure immigrant settlement still exists (might have been abandoned?) - belt-and-suspenders check
                        if immigrant.id not in self.settlements: continue

                        dist = self._calculate_distance(emigrant, immigrant)
                        if dist < min_dist:
                            min_dist = dist
                            best_target = immigrant # Found a closer target

                    # If a suitable target was found
                    if best_target:
                        # Calculate number of migrants
                        num_to_migrate = int(emigrant.population * migration_max_percentage)
                        num_to_migrate = max(1, num_to_migrate) # Migrate at least 1 person
                        # Ensure at least 1 person is left behind
                        num_to_migrate = min(num_to_migrate, emigrant.population - 1)

                        if num_to_migrate > 0:
                            # print(f"  Migrating {num_to_migrate} from {emigrant.name} (W:{emigrant.wealth:.0f}) to {best_target.name} (W:{best_target.wealth:.0f})")

                            # Update populations
                            emigrant.population -= num_to_migrate
                            best_target.population += num_to_migrate

                            # <<< Record migration details >>>
                            self.migration_details_this_tick.append({
                                'tick': self.tick,
                                'from_id': emigrant.id,
                                'from_name': emigrant.name,
                                'to_id': best_target.id,
                                'to_name': best_target.name,
                                'quantity': num_to_migrate
                            })

                            # Recalculate derived stats (labor, storage) for both settlements
                            # It's important to do this immediately after population change
                            emigrant.update_derived_stats()
                            best_target.update_derived_stats()

                            migrants_moved_total += num_to_migrate

                # if migrants_moved_total > 0:
                #      print(f"  Total migrants moved this tick: {migrants_moved_total}")
        # print(f"  Migration took: {time.time() - start_time:.4f}s")


# --- NO Main Execution Block Here ---
# This file is intended to be imported as a module.
