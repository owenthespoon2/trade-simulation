import random
import uuid
import math
import os
import time
from collections import defaultdict, OrderedDict
import json
import math # Ensure math is imported for ceil

# ==============================================================================
# FILE INDEX (Updated for Departure Tick)
# ==============================================================================
# - Data Structures (Good, ItemInstance) : Line 25
# - Settlement Class                      : Line 65
#   - __init__                            : Line 68
#   - _update_trade_capacity              : Line 120
#   - update_derived_stats                : Line 133
#   - add_log                             : Line 152 (Uses config param)
#   - Storage Management (add/remove/get) : Line 157
#   - decide_upgrade                      : Line 203 (Uses config param)
#   - progress_upgrade                    : Line 230
#   - produce                             : Line 258
#   - consume                             : Line 330
#   - update_prices                       : Line 350
# - Region Class                          : Line 378
# - Civilization Class                    : Line 384
# - World Class                           : Line 390
#   - __init__                            : Line 392
#   - Entity Management (add/get)         : Line 416
#   - get_global_good_totals              : Line 424
#   - find_trade_opportunities            : Line 436
#   - execute_trades                      : Line 493 (Adds departure_tick to shipment)
#   - _calculate_distance                 : Line 650
#   - simulation_step                     : Line 655 (Adds Shipment Arrival Phase)
# ==============================================================================


# ==============================================================================
# Data Structures
# ==============================================================================

class Good:
    """Represents a type of good that can be produced, traded, and consumed."""
    def __init__(self, id, name, base_value, is_bulk=True, is_producible=False):
        self.id = id; self.name = name; self.base_value = base_value
        self.is_bulk = is_bulk; self.is_producible = is_producible
        self.recipe = None
    def __repr__(self): return f"Good({self.name})"
    def add_recipe(self, inputs, outputs, labor, required_terrain=None, wealth_cost=0):
        if not self.is_producible: print(f"WARN: Cannot add recipe to non-producible good: {self.name}"); return
        if not isinstance(inputs, dict): raise TypeError(f"Recipe inputs for {self.id} must be a dict")
        if not isinstance(outputs, dict): raise TypeError(f"Recipe outputs for {self.id} must be a dict")
        if not outputs: raise ValueError(f"Recipe for {self.id} must have outputs")
        self.recipe = {'inputs': inputs, 'outputs': outputs, 'labor': float(labor), 'required_terrain': required_terrain, 'wealth_cost': float(wealth_cost)}

class ItemInstance:
    """Represents a specific instance of a non-bulk good."""
    def __init__(self, good_id, origin_settlement_id, quantity=1, quality=1.0):
        self.instance_id = str(uuid.uuid4()); self.good_id = good_id
        self.origin_settlement_id = origin_settlement_id; self.current_location_settlement_id = origin_settlement_id
        self.quantity = quantity; self.quality = quality; self.trade_history = []
    def __repr__(self):
        history_summary = f", History: {len(self.trade_history)} steps" if self.trade_history else ""
        return (f"Item(ID: {self.instance_id[:4]}..., Good: {self.good_id}, "
                f"Origin: {self.origin_settlement_id}, Loc: {self.current_location_settlement_id}, "
                f"Qty: {self.quantity:.1f}{history_summary})")

# ==============================================================================
# Settlement Class
# ==============================================================================
class Settlement:
    """Represents a settlement, managing population, resources, production, etc."""
    def __init__(self, id, name, region_id, population, terrain_type,
                 sim_params, building_defs, # Now expects sim_params and building_defs
                 initial_wealth=None, x=0, y=0, z=0):
        """Initializes a Settlement."""
        self.id = id; self.name = name; self.region_id = region_id
        self.population = max(1, int(population))
        self.terrain_type = terrain_type
        self.x = float(x); self.y = float(y); self.z = float(z)

        # Store references to global parameters and definitions
        self.params = sim_params
        self.building_defs = building_defs

        # Storage
        self.bulk_storage = defaultdict(float)
        self.item_storage = defaultdict(list)

        # Economic state
        self.consumption_needs = defaultdict(lambda: 1.0)
        self.local_prices = {}
        self.wealth = float(initial_wealth if initial_wealth is not None else self.params.get('settlement_default_initial_wealth', 500))
        self.log = []
        self.production_this_tick = defaultdict(float)

        # Building / Capacity State
        self.market_level = 1
        self.trade_capacity = 0
        self.trades_executed_this_tick = 0
        self.failed_trades_max_capacity_counter = 0
        self.is_upgrading = None

        # Store base parameters needed for dynamic calculation
        self._storage_capacity_per_pop = float(self.params.get('storage_capacity_per_pop', 10.0))
        self._labor_per_pop = float(self.params.get('labor_per_pop', 0.5))
        self._city_pop_threshold = int(self.params.get('city_population_threshold', 150))
        self._city_storage_multiplier = float(self.params.get('city_storage_multiplier', 1.5))

        # Initial calculation of derived stats
        self.max_labor_pool = 0.0; self.storage_capacity = 0.0; self.current_labor_pool = 0.0
        self.update_derived_stats()
        self._update_trade_capacity() # Calculate initial trade capacity

        # State for Abandonment tracking
        self.ticks_below_wealth_threshold = 0
        self.is_abandoned = False

    def _update_trade_capacity(self):
        """Calculates the settlement's trade capacity based on its market level."""
        base_capacity = self.params.get('base_trade_capacity', 5)
        bonus = 0
        market_def = self.building_defs.get('market', {}).get('levels', {})
        for level in range(1, self.market_level + 1):
            level_str = str(level)
            if level_str in market_def:
                bonus += market_def[level_str].get('trade_capacity_bonus', 0)
        self.trade_capacity = base_capacity + bonus

    def update_derived_stats(self):
        """Recalculates stats based on current population."""
        self.population = max(1, self.population)
        self.max_labor_pool = self.population * self._labor_per_pop
        self.current_labor_pool = self.max_labor_pool
        base_capacity = self.population * self._storage_capacity_per_pop
        if self.population >= self._city_pop_threshold:
            self.storage_capacity = base_capacity * self._city_storage_multiplier
        else:
            self.storage_capacity = base_capacity

    def __repr__(self):
        """String representation of the Settlement."""
        return (f"Settlement({self.name}, Pop: {self.population}, "
                f"Wealth: {self.wealth:.0f}, MktLvl: {self.market_level}, Trades: {self.trades_executed_this_tick}/{self.trade_capacity}, "
                f"Terrain: {self.terrain_type}, Pos:({self.x:.0f},{self.y:.0f},{self.z:.0f}))")

    def add_log(self, message, tick):
        """Adds a timestamped message to the settlement's short event log."""
        max_len = self.params.get('settlement_log_max_length', 10) # Use config param
        self.log.append(f"T{tick}: {message}")
        self.log = self.log[-max_len:] # Keep only the last N messages

    # --- Storage Management ---
    def get_total_stored(self, good_id):
        bulk_qty = self.bulk_storage.get(good_id, 0.0)
        item_qty = sum(item.quantity for item in self.item_storage.get(good_id, []))
        return bulk_qty + item_qty

    def get_current_storage_load(self):
        total_bulk = sum(self.bulk_storage.values())
        total_items = sum(item.quantity for items in self.item_storage.values() for item in items)
        return total_bulk + total_items

    def add_to_storage(self, good, quantity=None, item_instance=None, tick=0):
        """Adds goods to storage, returns the actual quantity added."""
        current_load = self.get_current_storage_load()
        available_capacity = max(0.0, self.storage_capacity - current_load)
        added_qty = 0.0
        if available_capacity <= 1e-6: return 0.0 # No space

        if item_instance: # Handle non-bulk items
            needed_capacity = item_instance.quantity
            if needed_capacity <= available_capacity:
                self.item_storage[item_instance.good_id].append(item_instance)
                item_instance.current_location_settlement_id = self.id
                added_qty = item_instance.quantity
            # else: Cannot fit the whole item instance
        elif good and quantity is not None: # Handle bulk goods
            amount_to_add = min(quantity, available_capacity)
            if amount_to_add > 1e-6:
                if good.is_bulk:
                    self.bulk_storage[good.id] += amount_to_add
                else: # Should ideally not happen if item_instance is used for non-bulk
                    print(f"WARN T{tick}: Adding non-bulk {good.id} as quantity to {self.id}, creating new instance.")
                    self.item_storage[good.id].append(ItemInstance(good.id, self.id, quantity=amount_to_add))
                added_qty = amount_to_add

        return added_qty

    def remove_from_storage(self, good_id, quantity, tick=0):
        """Removes goods from storage, returns actual quantity removed and any item instances consumed."""
        removed_qty = 0.0; consumed_instances = []
        if good_id in self.bulk_storage: # Handle bulk goods first
            take_from_bulk = min(quantity, self.bulk_storage[good_id])
            self.bulk_storage[good_id] -= take_from_bulk; removed_qty += take_from_bulk
            if self.bulk_storage[good_id] < 1e-6: del self.bulk_storage[good_id]

        remaining_needed = quantity - removed_qty
        if remaining_needed > 1e-6 and good_id in self.item_storage: # Handle non-bulk items
            items_list = self.item_storage[good_id]; indices_to_remove = []
            for i, item in enumerate(items_list):
                if remaining_needed <= 1e-6: break
                take_from_item = min(remaining_needed, item.quantity)
                # Create a representation of the consumed part (important for trades)
                consumed_instance_part = ItemInstance(good_id=item.good_id, origin_settlement_id=item.origin_settlement_id, quantity=take_from_item, quality=item.quality)
                consumed_instance_part.instance_id = item.instance_id # Keep original ID
                consumed_instance_part.trade_history = item.trade_history[:] # Copy history
                consumed_instances.append(consumed_instance_part)

                item.quantity -= take_from_item; removed_qty += take_from_item; remaining_needed -= take_from_item
                if item.quantity < 1e-6: indices_to_remove.append(i) # Mark item for removal if fully consumed

            # Remove fully consumed items from storage
            for i in sorted(indices_to_remove, reverse=True): del items_list[i]
            if not self.item_storage[good_id]: del self.item_storage[good_id] # Clean up empty list

        return removed_qty, consumed_instances

    # --- Construction / Upgrade Logic ---
    def decide_upgrade(self, world_tick):
        """Basic AI to decide if the settlement should attempt to upgrade its market."""
        upgrade_trigger_threshold = self.params.get('market_upgrade_fail_trigger', 5)
        if self.is_upgrading: return
        if self.failed_trades_max_capacity_counter >= upgrade_trigger_threshold:
            next_level = self.market_level + 1
            market_def = self.building_defs.get('market', {}).get('levels', {})
            next_level_str = str(next_level)
            if next_level_str in market_def:
                cost_def = market_def[next_level_str].get('upgrade_cost')
                if cost_def:
                    can_afford_resources = True; needed_labor = cost_def.get('labor', 0)
                    if self.current_labor_pool < needed_labor: can_afford_resources = False
                    if can_afford_resources:
                        for good_id, required_qty in cost_def.items():
                            if good_id != 'labor' and self.get_total_stored(good_id) < required_qty:
                                can_afford_resources = False; break
                    if can_afford_resources:
                        print(f"INFO T{world_tick}: {self.name} starting upgrade to Market Level {next_level}.")
                        self.add_log(f"Starting upgrade: Market Lvl {next_level}", world_tick)
                        self.is_upgrading = {'building': 'market', 'level': next_level, 'cost': cost_def, 'cost_paid': False}
                        self.failed_trades_max_capacity_counter = 0
            else:
                 self.failed_trades_max_capacity_counter = 0

    def progress_upgrade(self, world_tick, all_goods_dict):
        """Processes the current upgrade project (deducts cost, completes build)."""
        if not self.is_upgrading: return
        if not self.is_upgrading['cost_paid']:
            cost = self.is_upgrading['cost']; can_pay = True; labor_cost = cost.get('labor', 0)
            if self.current_labor_pool < labor_cost: can_pay = False
            else: self.current_labor_pool -= labor_cost
            removed_quantities = {}
            if can_pay:
                for good_id, required_qty in cost.items():
                    if good_id != 'labor':
                        removed_qty, _ = self.remove_from_storage(good_id, required_qty, tick=world_tick)
                        if removed_qty < required_qty * 0.999:
                            can_pay = False; self.current_labor_pool += labor_cost
                            for gid, qty in removed_quantities.items(): self.add_to_storage(all_goods_dict[gid], quantity=qty, tick=world_tick)
                            print(f"WARN T{world_tick}: {self.name} failed upgrade payment (cannot afford {good_id}). Cancelling.")
                            self.add_log(f"Upgrade cancelled (lack {good_id})", world_tick)
                            break
                        else: removed_quantities[good_id] = removed_qty
            if not can_pay: self.is_upgrading = None; return
            self.is_upgrading['cost_paid'] = True
            self.add_log(f"Paid cost for Market Lvl {self.is_upgrading['level']}", world_tick)

        if self.is_upgrading['cost_paid']:
            building_type = self.is_upgrading['building']; new_level = self.is_upgrading['level']
            if building_type == 'market':
                self.market_level = new_level; self._update_trade_capacity()
                print(f"INFO T{world_tick}: {self.name} completed upgrade to Market Level {new_level}! New capacity: {self.trade_capacity}")
                self.add_log(f"Upgrade complete: Market Lvl {new_level}", world_tick)
            self.is_upgrading = None

    # --- Economic Actions ---
    def produce(self, all_goods_dict, world_tick):
        """Attempts to produce goods, tracks produced amounts."""
        max_production_passes = self.params.get('max_production_passes', 5)
        production_wealth_buffer = self.params.get('production_wealth_buffer', 0.0)
        self.production_this_tick.clear()
        if self.wealth < production_wealth_buffer: return
        self.current_labor_pool = self.max_labor_pool

        for _pass in range(max_production_passes):
            production_possible_in_pass = False
            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            if not producible_goods: break
            producible_items = list(producible_goods.items()); random.shuffle(producible_items)
            for good_id, good in producible_items:
                recipe = good.recipe
                if recipe['required_terrain'] and self.terrain_type not in recipe['required_terrain']: continue
                if self.current_labor_pool < recipe['labor'] or self.wealth < recipe['wealth_cost']: continue
                inputs_available = True; required_inputs = recipe['inputs']
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        if self.get_total_stored(input_good_id) < input_qty: inputs_available = False; break
                    if not inputs_available: continue
                original_labor = self.current_labor_pool; original_wealth = self.wealth
                temp_input_storage_state = {}; temp_output_storage_state = {}
                self.current_labor_pool -= recipe['labor']; self.wealth -= recipe['wealth_cost']
                inputs_consumed_successfully = True
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        temp_input_storage_state[input_good_id] = self.get_total_stored(input_good_id)
                        removed_qty, _ = self.remove_from_storage(input_good_id, input_qty, tick=world_tick)
                        if removed_qty < input_qty * 0.999:
                            inputs_consumed_successfully = False; self.current_labor_pool = original_labor; self.wealth = original_wealth
                            for gid, initial_qty in temp_input_storage_state.items():
                                 current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                                 if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                            break
                    if not inputs_consumed_successfully: continue
                outputs_produced_successfully = True; actual_added_quantities = {}
                for output_good_id, output_qty in recipe['outputs'].items():
                    output_good = all_goods_dict[output_good_id]
                    temp_output_storage_state[output_good_id] = self.get_total_stored(output_good_id)
                    added_qty = self.add_to_storage(output_good, quantity=output_qty, tick=world_tick)
                    actual_added_quantities[output_good_id] = added_qty
                    if added_qty < output_qty * 0.999:
                        outputs_produced_successfully = False; self.current_labor_pool = original_labor; self.wealth = original_wealth
                        for gid, initial_qty in temp_input_storage_state.items():
                             current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                             if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                        for gid, initial_qty in temp_output_storage_state.items():
                            current_qty = self.get_total_stored(gid); qty_to_remove = current_qty - initial_qty
                            if qty_to_remove > 1e-6: self.remove_from_storage(gid, qty_to_remove)
                        break
                if not outputs_produced_successfully: continue
                for output_good_id, added_qty in actual_added_quantities.items():
                    if added_qty > 1e-6: self.production_this_tick[output_good_id] += added_qty
                production_possible_in_pass = True
            if not production_possible_in_pass: break

    def consume(self, goods_dict, world_tick):
        """Simulates consumption of goods by the population."""
        base_consumption_rate = self.params.get('base_consumption_rate', 0.1)
        city_pop_threshold = self.params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold
        for good_id, good in goods_dict.items():
            if good_id in ['iron_ore', 'seed']: continue
            consume_this = (good_id == 'bread' and is_city) or \
                           (good_id != 'bread' and not (good_id == 'grain' and is_city))
            if consume_this:
                demand_modifier = self.consumption_needs[good_id]
                amount_needed = max(0, base_consumption_rate * self.population * demand_modifier * (1 + random.uniform(-0.1, 0.1)))
                if amount_needed > 0.01:
                    available = self.get_total_stored(good_id)
                    amount_to_consume = min(amount_needed, available)
                    if amount_to_consume > 0.01:
                        self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)

    def update_prices(self, goods_dict, world_tick):
        """Updates local prices based on supply and demand estimates."""
        base_consumption_rate = self.params.get('base_consumption_rate', 0.1)
        price_sensitivity = self.params.get('price_sensitivity', 2.0)
        min_price_multiplier = self.params.get('min_price_multiplier', 0.1)
        max_price_multiplier = self.params.get('max_price_multiplier', 10.0)
        city_pop_threshold = self.params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold
        for good_id, good in goods_dict.items():
            supply = max(self.get_total_stored(good_id), 0.01)
            demand_estimate = 0.01
            if good_id not in ['iron_ore', 'seed']:
                if (good_id == 'bread' and is_city) or \
                   (good_id != 'bread' and not (good_id == 'grain' and is_city)):
                    demand_estimate = max(0.01, base_consumption_rate * self.population * self.consumption_needs[good_id])
            ratio = supply / demand_estimate
            price_modifier = math.pow(ratio, -price_sensitivity)
            min_price = good.base_value * min_price_multiplier; max_price = good.base_value * max_price_multiplier
            new_price = good.base_value * price_modifier
            self.local_prices[good_id] = max(min_price, min(new_price, max_price))

# ==============================================================================
# Region & Civilization Classes (Unchanged)
# ==============================================================================
class Region:
    def __init__(self, id, name, resource_modifiers=None): self.id = id; self.name = name; self.resource_modifiers = resource_modifiers if resource_modifiers else {}; self.settlements = []
    def add_settlement(self, settlement): self.settlements.append(settlement)
class Civilization:
    def __init__(self, id, name): self.id = id; self.name = name; self.regions = []
    def add_region(self, region): self.regions.append(region)

# ==============================================================================
# World Class
# ==============================================================================
class World:
    """Manages the overall simulation state and orchestrates the simulation loop."""
    def __init__(self, sim_params, building_defs):
        """Initializes the World object."""
        self.tick = 0; self.goods = OrderedDict(); self.settlements = OrderedDict()
        self.regions = OrderedDict(); self.civilizations = OrderedDict(); self.trade_routes = {}
        self.recent_trades_log = []; self.executed_trade_details_this_tick = []
        self.potential_trades_this_tick = []; self.failed_trades_this_tick = []
        self.migration_details_this_tick = []
        self.params = sim_params
        self.building_defs = building_defs
        self.in_transit_shipments = []
        self.transport_cost_per_distance_unit = float(self.params.get('transport_cost_per_distance_unit', 0.0))
        self.max_trade_cost_wealth_percentage = float(self.params.get('max_trade_cost_wealth_percentage', 1.0))
        self.base_transport_speed = float(self.params.get('base_transport_speed', 1.0))
        if self.base_transport_speed <= 0: self.base_transport_speed = 1.0
        print(f"World initialized. Transport Cost/Dist: {self.transport_cost_per_distance_unit}, "
              f"Max Trade % Wealth: {self.max_trade_cost_wealth_percentage:.2f}, "
              f"Transport Speed: {self.base_transport_speed}")

    # --- Entity Management ---
    def add_good(self, good): self.goods[good.id] = good
    def add_settlement(self, settlement): self.settlements[settlement.id] = settlement
    def add_region(self, region): self.regions[region.id] = region
    def add_civilization(self, civilization): self.civilizations[civilization.id] = civilization
    def get_all_settlements(self): return list(self.settlements.values())

    # --- Global State Calculation ---
    def get_global_good_totals(self):
        """Calculates the total amount of each good across all active settlements."""
        totals = defaultdict(float)
        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]
        for good_id in self.goods.keys():
            total_qty = sum(s.get_total_stored(good_id) for s in active_settlements)
            if total_qty > 1e-6: totals[good_id] = total_qty
        return dict(totals)

    # --- Trade Logic ---
    def find_trade_opportunities(self):
        """
        Identifies potential trade opportunities based on price differences,
        considering transport costs.
        """
        self.potential_trades_this_tick.clear(); opportunities_for_execution = []
        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]
        min_trade_qty = self.params.get('min_trade_qty', 0.01)
        transport_cost_rate = self.transport_cost_per_distance_unit

        for i in range(len(active_settlements)):
            for j in range(i + 1, len(active_settlements)):
                s_a, s_b = active_settlements[i], active_settlements[j]
                distance = self._calculate_distance(s_a, s_b)

                for good_id, good in self.goods.items():
                    price_a = s_a.local_prices.get(good_id); price_b = s_b.local_prices.get(good_id)
                    if price_a is None or price_b is None or price_a <= 1e-6 or price_b <= 1e-6: continue

                    transport_cost_per_unit = distance * transport_cost_rate
                    potential_profit, seller, buyer, qty_avail = 0, None, None, 0.0
                    seller_price, buyer_price = 0.0, 0.0

                    if price_b > price_a + transport_cost_per_unit:
                        potential_profit = price_b - price_a
                        seller, buyer = s_a, s_b; seller_price, buyer_price = price_a, price_b
                        qty_avail = seller.get_total_stored(good_id)
                    elif price_a > price_b + transport_cost_per_unit:
                        potential_profit = price_a - price_b
                        seller, buyer = s_b, s_a; seller_price, buyer_price = price_b, price_a
                        qty_avail = seller.get_total_stored(good_id)

                    if seller is not None and qty_avail > 1e-6:
                        potential_qty = qty_avail
                        if not good.is_bulk and good_id in seller.item_storage:
                            potential_qty = seller.item_storage[good_id][0].quantity if seller.item_storage[good_id] else 0

                        if potential_qty < min_trade_qty: potential_qty = 0

                        min_qty_goods_cost = seller_price * min_trade_qty
                        min_qty_transport_cost = transport_cost_per_unit * min_trade_qty
                        min_qty_total_cost = min_qty_goods_cost + min_qty_transport_cost

                        is_viable_prelim = (potential_profit > transport_cost_per_unit and potential_qty >= min_trade_qty and buyer.wealth >= min_qty_total_cost)

                        self.potential_trades_this_tick.append({
                            'seller_id': seller.id, 'buyer_id': buyer.id, 'seller_name': seller.name, 'buyer_name': buyer.name,
                            'good_id': good.id, 'good_name': good.name, 'seller_price': seller_price, 'buyer_price': buyer_price,
                            'potential_profit_per_unit': potential_profit, 'transport_cost_per_unit': transport_cost_per_unit,
                            'qty_avail': qty_avail, 'potential_qty': potential_qty, 'distance': distance,
                            'is_viable_prelim': is_viable_prelim
                        })

                        if is_viable_prelim:
                            opportunities_for_execution.append({
                                'from': seller, 'to': buyer, 'good': good,
                                'potential_profit_per_unit': potential_profit,
                                'transport_cost_per_unit': transport_cost_per_unit,
                                'potential_qty': potential_qty, 'seller_price': seller_price,
                                'buyer_price': buyer_price, 'distance': distance
                            })

        opportunities_for_execution.sort(key=lambda x: x['potential_profit_per_unit'], reverse=True)
        return opportunities_for_execution

    def execute_trades(self, opportunities):
        """
        Attempts to execute trades: checks capacity, costs, budget, removes goods
        from seller, transfers wealth, and creates an in-transit shipment record.
        """
        trades_executed_log_entries = []; self.executed_trade_details_this_tick.clear(); self.failed_trades_this_tick.clear()
        trades_count_global = 0; max_trades_global = self.params.get('max_trades_per_tick', 200)
        min_trade_qty = self.params.get('min_trade_qty', 0.01)
        log_max_len = self.params.get('world_trade_log_max_length', 10)
        transport_cost_rate = self.transport_cost_per_distance_unit
        max_trade_pct = self.max_trade_cost_wealth_percentage
        transport_speed = self.base_transport_speed

        current_settlements_state = self.settlements.copy()

        for i, trade in enumerate(opportunities):
            # --- Initial Setup & Checks ---
            seller_obj = current_settlements_state.get(trade['from'].id)
            buyer_obj = current_settlements_state.get(trade['to'].id)
            good = trade['good']
            potential_profit = trade['potential_profit_per_unit']; seller_potential_qty = trade['potential_qty']
            seller_price = trade['seller_price']
            distance = trade['distance']
            transport_cost_per_unit = trade['transport_cost_per_unit']
            fail_reason = ""

            if not seller_obj or not buyer_obj or seller_obj.is_abandoned or buyer_obj.is_abandoned:
                 fail_reason = "Settlement abandoned/removed"; self.failed_trades_this_tick.append({'seller_id': trade['from'].id, 'buyer_id': trade['to'].id, 'good_id': good.id, 'fail_reason': fail_reason, 'tick': self.tick}); continue

            fail_log_base = {'seller_id': seller_obj.id, 'buyer_id': buyer_obj.id, 'seller_name': seller_obj.name, 'buyer_name': buyer_obj.name, 'good_id': good.id, 'good_name': good.name, 'seller_price': seller_price, 'buyer_price': trade['buyer_price'], 'potential_profit_per_unit': potential_profit, 'transport_cost_per_unit': transport_cost_per_unit, 'potential_qty': seller_potential_qty, 'qty_avail': seller_obj.get_total_stored(good.id)}

            if trades_count_global >= max_trades_global: fail_reason = "Skipped (Global Max Trades)"; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            if seller_obj.trades_executed_this_tick >= seller_obj.trade_capacity:
                fail_reason = f"Seller max trades ({seller_obj.trades_executed_this_tick}/{seller_obj.trade_capacity})"; seller_obj.failed_trades_max_capacity_counter += 1; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue
            if buyer_obj.trades_executed_this_tick >= buyer_obj.trade_capacity:
                fail_reason = f"Buyer max trades ({buyer_obj.trades_executed_this_tick}/{buyer_obj.trade_capacity})"; buyer_obj.failed_trades_max_capacity_counter += 1; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # --- Determine Trade Quantity ---
            trade_qty = 0.0
            item_to_trade_instance_id = None
            cost_per_unit_total = seller_price + transport_cost_per_unit
            initial_calc_trade_qty = 0.0
            budget_limited = False

            if good.is_bulk:
                max_affordable_qty = float('inf')
                if cost_per_unit_total > 1e-6: max_affordable_qty = buyer_obj.wealth / cost_per_unit_total
                buyer_storage = max(0.0, buyer_obj.storage_capacity - buyer_obj.get_current_storage_load())
                initial_calc_trade_qty = min(seller_potential_qty, max_affordable_qty, buyer_storage)
                trade_qty = initial_calc_trade_qty
            else: # Non-bulk
                 if good.id in seller_obj.item_storage and seller_obj.item_storage[good.id]:
                    item = seller_obj.item_storage[good.id][0]; item_qty = item.quantity
                    item_total_cost = (seller_price + transport_cost_per_unit) * item_qty
                    if buyer_obj.wealth < item_total_cost:
                        fail_reason = f"Buyer Cannot Afford Non-Bulk + Transport ({buyer_obj.wealth:.1f}<{item_total_cost:.1f})"
                        self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue
                    max_cost_allowed = buyer_obj.wealth * max_trade_pct
                    if item_total_cost > max_cost_allowed:
                        fail_reason = f"Non-Bulk Cost ({item_total_cost:.1f}) Exceeds Budget ({max_cost_allowed:.1f})"
                        self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue
                    trade_qty = item.quantity; item_to_trade_instance_id = item.instance_id
                    initial_calc_trade_qty = trade_qty
                 else:
                    fail_reason = "Seller Lacks Non-Bulk Item (Exec)"; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # --- Apply Wealth Percentage Budget Limit (Bulk) ---
            if good.is_bulk and trade_qty > 1e-6:
                max_cost_allowed = buyer_obj.wealth * max_trade_pct
                max_qty_by_budget = float('inf')
                if cost_per_unit_total > 1e-6: max_qty_by_budget = max_cost_allowed / cost_per_unit_total
                if trade_qty > max_qty_by_budget + 1e-6: budget_limited = True
                trade_qty = min(trade_qty, max_qty_by_budget)

            # --- Check Minimum Quantity ---
            if trade_qty < min_trade_qty:
                 if seller_potential_qty < min_trade_qty: fail_reason = "Seller stock < min"
                 elif 'max_affordable_qty' in locals() and max_affordable_qty < min_trade_qty: fail_reason = "Buyer cannot afford min qty (+ transport)"
                 elif 'buyer_storage' in locals() and buyer_storage < min_trade_qty: fail_reason = "Buyer storage < min qty"
                 elif budget_limited: fail_reason = f"Qty limited by budget ({trade_qty:.3f}) & < min"
                 else: fail_reason = f"Calc trade qty ({trade_qty:.3f}) < min"
                 self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # --- Final Feasibility Check ---
            total_goods_cost = seller_price * trade_qty
            total_transport_cost = transport_cost_per_unit * trade_qty
            total_transaction_cost = total_goods_cost + total_transport_cost
            can_afford = buyer_obj.wealth >= (total_transaction_cost - 1e-6)
            has_stock = seller_obj.get_total_stored(good.id) >= (trade_qty - 1e-6)
            if not can_afford: fail_reason += f"Buyer Cannot Afford Final Qty ({buyer_obj.wealth:.1f}<{total_transaction_cost:.1f}); "
            if not has_stock: fail_reason += f"Seller Lacks Final Stock ({seller_obj.get_total_stored(good.id):.1f}<{trade_qty:.1f}); "

            # --- Execute Transaction (Remove goods, Transfer wealth, Create Shipment) ---
            if can_afford and has_stock:
                # 1. Remove goods from seller
                removed_qty, consumed_instances = seller_obj.remove_from_storage(good.id, trade_qty, tick=self.tick)
                if removed_qty < trade_qty * 0.999: # Check if removal succeeded
                    fail_reason += f"Failed Stock Removal ({removed_qty:.1f}/{trade_qty:.1f})";
                    if consumed_instances: seller_obj.add_to_storage(good, item_instance=consumed_instances[0], tick=self.tick)
                    elif removed_qty > 1e-6: seller_obj.add_to_storage(good, quantity=removed_qty, tick=self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()}); continue

                # 2. Transfer wealth (happens immediately)
                final_goods_cost = seller_price * removed_qty
                final_transport_cost = transport_cost_per_unit * removed_qty
                final_total_cost_buyer = final_goods_cost + final_transport_cost
                seller_obj.wealth += final_goods_cost
                buyer_obj.wealth -= final_total_cost_buyer

                # 3. Create Shipment Record
                travel_ticks = max(1, math.ceil(distance / transport_speed))
                arrival_tick = self.tick + travel_ticks
                departure_tick = self.tick # NEW: Store departure tick

                shipment_item_instance = None
                if not good.is_bulk and consumed_instances:
                    shipment_item_instance = consumed_instances[0]
                    shipment_item_instance.trade_history.append((seller_obj.id, seller_price, self.tick))

                shipment = {
                    'departure_tick': departure_tick, # NEW
                    'arrival_tick': arrival_tick,
                    'buyer_id': buyer_obj.id,
                    'seller_id': seller_obj.id,
                    'good_id': good.id,
                    'quantity': removed_qty,
                    'item_instance': shipment_item_instance,
                    # Add unique ID for easier UI tracking
                    'shipment_id': f"{seller_obj.id}-{buyer_obj.id}-{good.id}-{departure_tick}-{random.randint(1000,9999)}"
                }
                self.in_transit_shipments.append(shipment)

                # 4. Log successful trade initiation
                seller_obj.trades_executed_this_tick += 1; buyer_obj.trades_executed_this_tick += 1
                trade_log_msg = (f"T{self.tick}: SHIP {seller_obj.name} -> {buyer_obj.name}, {removed_qty:.2f} {good.name} "
                                 f"@ {seller_price:.2f} (Cost: {final_goods_cost:.2f}, TCost: {final_transport_cost:.2f}) "
                                 f"ETA: T{arrival_tick}")
                trades_executed_log_entries.append(trade_log_msg)
                self.executed_trade_details_this_tick.append({
                    'seller_id': seller_obj.id, 'buyer_id': buyer_obj.id, 'seller_name': seller_obj.name, 'buyer_name': buyer_obj.name,
                    'good_id': good.id, 'good_name': good.name, 'quantity': removed_qty, 'seller_price': seller_price,
                    'buyer_price': trade['buyer_price'], 'potential_profit_per_unit': potential_profit,
                    'transport_cost_per_unit': transport_cost_per_unit, 'transport_cost_total': final_transport_cost,
                    'tick': self.tick, 'arrival_tick': arrival_tick
                })
                trades_count_global += 1

            else: # Failed final feasibility check
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})

        # Update recent trades log
        self.recent_trades_log = trades_executed_log_entries + self.recent_trades_log; self.recent_trades_log = self.recent_trades_log[:log_max_len]


    # --- Utility Methods ---
    def _calculate_distance(self, s1, s2):
        """Calculate Euclidean distance between two settlements in 3D space."""
        return math.sqrt((s1.x - s2.x)**2 + (s1.y - s2.y)**2 + (s1.z - s2.z)**2)

    # ==========================================================================
    # Main Simulation Step
    # ==========================================================================
    def simulation_step(self):
        """Executes one full tick of the simulation cycle."""
        self.tick += 1

        # --- Reset Per-Tick Counters ---
        self.executed_trade_details_this_tick.clear(); self.potential_trades_this_tick.clear()
        self.failed_trades_this_tick.clear(); self.migration_details_this_tick.clear()
        for settlement in self.settlements.values():
            if not settlement.is_abandoned:
                settlement.trades_executed_this_tick = 0
                settlement.production_this_tick.clear()

        # --- Get Current Active Settlements ---
        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]

        # --- Shipment Arrival Phase ---
        remaining_shipments = []
        shipments_arrived_count = 0
        for shipment in self.in_transit_shipments:
            if self.tick >= shipment['arrival_tick']:
                buyer = self.settlements.get(shipment['buyer_id'])
                if buyer and not buyer.is_abandoned:
                    good_obj = self.goods.get(shipment['good_id'])
                    if good_obj:
                        added_qty = buyer.add_to_storage(
                            good=good_obj,
                            quantity=shipment['quantity'] if good_obj.is_bulk else None,
                            item_instance=shipment['item_instance'],
                            tick=self.tick
                        )
                        if added_qty < shipment['quantity'] * 0.999:
                            lost_qty = shipment['quantity'] - added_qty
                            fail_msg = (f"T{self.tick}: Arrival Fail {shipment['seller_id']}->{buyer.id}: "
                                        f"{lost_qty:.1f}/{shipment['quantity']:.1f} {shipment['good_id']} lost (No Storage)")
                            print(f"WARN: {fail_msg}")
                            buyer.add_log(f"Shipment arrival failed (storage full), {lost_qty:.1f} {shipment['good_id']} lost", self.tick)
                        else:
                             buyer.add_log(f"Shipment arrived from {shipment['seller_id']}: {added_qty:.1f} {shipment['good_id']}", self.tick)
                        shipments_arrived_count += 1
                    else:
                        print(f"ERROR T{self.tick}: Good {shipment['good_id']} not found for arriving shipment to {shipment['buyer_id']}.")
                else:
                    print(f"WARN T{self.tick}: Buyer {shipment['buyer_id']} not found/abandoned for shipment arrival. Goods lost.")
            else:
                remaining_shipments.append(shipment)
        self.in_transit_shipments = remaining_shipments


        # --- Construction Progress Phase ---
        for settlement in active_settlements:
             settlement.progress_upgrade(self.tick, self.goods)

        # --- Core Economic Phases ---
        for settlement in active_settlements: settlement.produce(self.goods, self.tick)
        for settlement in active_settlements: settlement.consume(self.goods, self.tick)
        for settlement in active_settlements: settlement.update_prices(self.goods, self.tick)

        # --- Trade Phase (Initiates new shipments) ---
        opportunities = self.find_trade_opportunities()
        self.execute_trades(opportunities)

        # --- Upgrade Decision Phase ---
        for settlement in active_settlements:
            settlement.decide_upgrade(self.tick)

        # --- Upkeep Phase ---
        storage_cost_rate = self.params.get('storage_cost_per_unit', 0.0)
        if storage_cost_rate > 0:
            for settlement in active_settlements:
                upkeep = settlement.get_current_storage_load() * storage_cost_rate
                if upkeep > 0: settlement.wealth -= upkeep

        # --- Abandonment Check Phase ---
        settlements_to_remove_ids = []
        abandonment_wealth_threshold = self.params.get('abandonment_wealth_threshold', -100)
        abandonment_ticks_threshold = self.params.get('abandonment_ticks_threshold', 15)
        for settlement_id in list(self.settlements.keys()):
            settlement = self.settlements[settlement_id]
            if settlement.is_abandoned: continue
            if settlement.wealth < abandonment_wealth_threshold: settlement.ticks_below_wealth_threshold += 1
            else: settlement.ticks_below_wealth_threshold = 0
            if settlement.ticks_below_wealth_threshold >= abandonment_ticks_threshold:
                settlement.is_abandoned = True; settlements_to_remove_ids.append(settlement.id)
                print(f"INFO: Settlement {settlement.name} ({settlement.id}) abandoned at tick {self.tick} (Low Wealth: {settlement.wealth:.0f}).")
                self.recent_trades_log.insert(0, f"T{self.tick}: {settlement.name} abandoned!"); self.recent_trades_log = self.recent_trades_log[:self.params.get('world_trade_log_max_length', 10)]

        if settlements_to_remove_ids:
            for settlement_id in settlements_to_remove_ids:
                if settlement_id in self.settlements: del self.settlements[settlement_id]


        # --- Migration Phase ---
        migration_interval = self.params.get('migration_check_interval', 5)
        if self.tick % migration_interval == 0 and len(self.settlements) > 1:
            migration_wealth_threshold = self.params.get('migration_wealth_threshold', 0)
            migration_target_min_wealth = self.params.get('migration_target_min_wealth', 600)
            migration_max_percentage = self.params.get('migration_max_percentage', 0.1)
            current_active_settlements = list(self.settlements.values())
            potential_emigrants = [s for s in current_active_settlements if s.wealth < migration_wealth_threshold and s.population > 1]
            potential_immigrants = [s for s in current_active_settlements if s.wealth >= migration_target_min_wealth]
            if potential_emigrants and potential_immigrants:
                migrants_moved_total = 0
                for emigrant in potential_emigrants:
                    if emigrant.id not in self.settlements or emigrant.population <= 1: continue
                    best_target = None; min_dist = float('inf')
                    for immigrant in potential_immigrants:
                        if immigrant.id not in self.settlements or emigrant.id == immigrant.id: continue
                        dist = self._calculate_distance(emigrant, immigrant)
                        if dist < min_dist: min_dist = dist; best_target = immigrant
                    if best_target:
                        if best_target.id not in self.settlements: continue
                        num_to_migrate = max(1, int(emigrant.population * migration_max_percentage))
                        num_to_migrate = min(num_to_migrate, emigrant.population - 1)
                        if num_to_migrate > 0:
                            emigrant.population -= num_to_migrate
                            best_target.population += num_to_migrate
                            self.migration_details_this_tick.append({'tick': self.tick, 'from_id': emigrant.id, 'from_name': emigrant.name,'to_id': best_target.id, 'to_name': best_target.name, 'quantity': num_to_migrate})
                            emigrant.update_derived_stats(); best_target.update_derived_stats()
                            migrants_moved_total += num_to_migrate

# --- NO Main Execution Block Here ---
