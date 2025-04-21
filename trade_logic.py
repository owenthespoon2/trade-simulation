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
# - Data Structures (Good, ItemInstance) : Line 20
# - Settlement Class                      : Line 60
#   - __init__                            : Line 63
#   - _update_trade_capacity              : Line 115
#   - update_derived_stats                : Line 128
#   - add_log                             : Line 147 (Uses config param)
#   - Storage Management (add/remove/get) : Line 152
#   - decide_upgrade                      : Line 198 (Uses config param)
#   - progress_upgrade                    : Line 225
#   - produce                             : Line 253
#   - consume                             : Line 325
#   - update_prices                       : Line 345
# - Region Class                          : Line 373
# - Civilization Class                    : Line 379
# - World Class                           : Line 385
#   - __init__                            : Line 387
#   - Entity Management (add/get)         : Line 404
#   - get_global_good_totals              : Line 412
#   - find_trade_opportunities            : Line 424 (Uses config param implicitly)
#   - execute_trades                      : Line 467 (Uses config param, updates log length)
#   - _calculate_distance                 : Line 576
#   - simulation_step                     : Line 581
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
                 sim_params, building_defs,
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
        current_load = self.get_current_storage_load()
        available_capacity = max(0.0, self.storage_capacity - current_load)
        added_qty = 0.0
        if available_capacity <= 1e-6: return 0.0
        if item_instance:
            needed_capacity = item_instance.quantity
            if needed_capacity <= available_capacity:
                self.item_storage[item_instance.good_id].append(item_instance)
                item_instance.current_location_settlement_id = self.id
                added_qty = item_instance.quantity
        elif good and quantity is not None:
            amount_to_add = min(quantity, available_capacity)
            if amount_to_add > 1e-6:
                if good.is_bulk: self.bulk_storage[good.id] += amount_to_add
                else: self.item_storage[good.id].append(ItemInstance(good.id, self.id, quantity=amount_to_add))
                added_qty = amount_to_add
        return added_qty

    def remove_from_storage(self, good_id, quantity, tick=0):
        removed_qty = 0.0; consumed_instances = []
        if good_id in self.bulk_storage:
            take_from_bulk = min(quantity, self.bulk_storage[good_id])
            self.bulk_storage[good_id] -= take_from_bulk; removed_qty += take_from_bulk
            if self.bulk_storage[good_id] < 1e-6: del self.bulk_storage[good_id]
        remaining_needed = quantity - removed_qty
        if remaining_needed > 1e-6 and good_id in self.item_storage:
            items_list = self.item_storage[good_id]; indices_to_remove = []
            for i, item in enumerate(items_list):
                if remaining_needed <= 1e-6: break
                take_from_item = min(remaining_needed, item.quantity)
                consumed_instance_part = ItemInstance(good_id=item.good_id, origin_settlement_id=item.origin_settlement_id, quantity=take_from_item, quality=item.quality)
                consumed_instance_part.instance_id = item.instance_id; consumed_instance_part.trade_history = item.trade_history[:]
                consumed_instances.append(consumed_instance_part)
                item.quantity -= take_from_item; removed_qty += take_from_item; remaining_needed -= take_from_item
                if item.quantity < 1e-6: indices_to_remove.append(i)
            for i in sorted(indices_to_remove, reverse=True): del items_list[i]
            if not self.item_storage[good_id]: del self.item_storage[good_id]
        return removed_qty, consumed_instances

    # --- Construction / Upgrade Logic ---
    def decide_upgrade(self, world_tick):
        """Basic AI to decide if the settlement should attempt to upgrade its market."""
        # Use config parameter for trigger threshold
        upgrade_trigger_threshold = self.params.get('market_upgrade_fail_trigger', 5)

        if self.is_upgrading: return

        if self.failed_trades_max_capacity_counter >= upgrade_trigger_threshold:
            # print(f"DEBUG T{world_tick}: {self.name} considering market upgrade (failed trades: {self.failed_trades_max_capacity_counter})")
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
                            if good_id != 'labor':
                                if self.get_total_stored(good_id) < required_qty: can_afford_resources = False; break
                    if can_afford_resources:
                        print(f"INFO T{world_tick}: {self.name} starting upgrade to Market Level {next_level}.")
                        self.add_log(f"Starting upgrade: Market Lvl {next_level}", world_tick)
                        self.is_upgrading = {'building': 'market', 'level': next_level, 'cost': cost_def, 'cost_paid': False}
                        self.failed_trades_max_capacity_counter = 0 # Reset counter
            else:
                 # print(f"DEBUG T{world_tick}: {self.name} already at max market level.")
                 self.failed_trades_max_capacity_counter = 0 # Reset counter

    def progress_upgrade(self, world_tick, all_goods_dict):
        """Processes the current upgrade project (deducts cost, completes build)."""
        if not self.is_upgrading: return

        if not self.is_upgrading['cost_paid']:
            # print(f"DEBUG T{world_tick}: {self.name} attempting to pay cost for {self.is_upgrading['building']} Lvl {self.is_upgrading['level']}")
            cost = self.is_upgrading['cost']; can_pay = True; labor_cost = cost.get('labor', 0)
            if self.current_labor_pool < labor_cost: can_pay = False
            else: self.current_labor_pool -= labor_cost
            removed_quantities = {}
            if can_pay:
                for good_id, required_qty in cost.items():
                    if good_id != 'labor':
                        removed_qty, _ = self.remove_from_storage(good_id, required_qty, tick=world_tick)
                        if removed_qty < required_qty * 0.999:
                            can_pay = False; self.current_labor_pool += labor_cost # Return labor
                            for gid, qty in removed_quantities.items(): self.add_to_storage(all_goods_dict[gid], quantity=qty, tick=world_tick) # Return goods
                            print(f"WARN T{world_tick}: {self.name} failed upgrade payment (cannot afford {good_id}). Cancelling.")
                            self.add_log(f"Upgrade cancelled (lack {good_id})", world_tick)
                            break
                        else: removed_quantities[good_id] = removed_qty
            if not can_pay: self.is_upgrading = None; return
            self.is_upgrading['cost_paid'] = True
            self.add_log(f"Paid cost for Market Lvl {self.is_upgrading['level']}", world_tick)

        if self.is_upgrading['cost_paid']: # Complete upgrade (instant build)
            building_type = self.is_upgrading['building']; new_level = self.is_upgrading['level']
            if building_type == 'market':
                self.market_level = new_level; self._update_trade_capacity()
                print(f"INFO T{world_tick}: {self.name} completed upgrade to Market Level {new_level}! New capacity: {self.trade_capacity}")
                self.add_log(f"Upgrade complete: Market Lvl {new_level}", world_tick)
            self.is_upgrading = None # Clear project

    # --- Economic Actions ---
    def produce(self, all_goods_dict, world_tick):
        """Attempts to produce goods, tracks produced amounts."""
        max_production_passes = self.params.get('max_production_passes', 5)
        production_wealth_buffer = self.params.get('production_wealth_buffer', 0.0)
        self.production_this_tick.clear() # Clear tracker
        if self.wealth < production_wealth_buffer: return
        self.current_labor_pool = self.max_labor_pool # Replenish labor

        for _pass in range(max_production_passes):
            production_possible_in_pass = False
            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            if not producible_goods: break
            producible_items = list(producible_goods.items()); random.shuffle(producible_items)
            for good_id, good in producible_items:
                recipe = good.recipe
                if recipe['required_terrain'] and self.terrain_type not in recipe['required_terrain']: continue
                if self.current_labor_pool < recipe['labor']: continue
                if self.wealth < recipe['wealth_cost']: continue
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
                # Success -> Update Tracker
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
            consume_this = False
            if good_id == 'bread' and is_city: consume_this = True
            elif good_id != 'bread' and not (good_id == 'grain' and is_city): consume_this = True
            if consume_this:
                demand_modifier = self.consumption_needs[good_id]
                amount_needed = (base_consumption_rate * self.population * demand_modifier * (1 + random.uniform(-0.1, 0.1)))
                amount_needed = max(0, amount_needed)
                if amount_needed > 0.01:
                    available = self.get_total_stored(good_id)
                    amount_to_consume = min(amount_needed, available)
                    if amount_to_consume > 0.01:
                        removed_qty, _ = self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)

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
                 if good_id == 'bread' and is_city: demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
                 elif good_id != 'bread' and not (good_id == 'grain' and is_city): demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
            demand_estimate = max(demand_estimate, 0.01)
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
        self.params = sim_params # Store sim parameters
        self.building_defs = building_defs # Store building definitions
        print(f"World initialized.")

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
        """Identifies potential trade opportunities based on price differences."""
        self.potential_trades_this_tick.clear(); opportunities_for_execution = []
        active_settlements = [s for s in self.settlements.values() if not s.is_abandoned]
        price_threshold = self.params.get('trade_profit_margin_threshold', 1.05)
        min_trade_qty = self.params.get('min_trade_qty', 0.01) # Use config param

        for i in range(len(active_settlements)):
            for j in range(i + 1, len(active_settlements)):
                s_a, s_b = active_settlements[i], active_settlements[j]
                for good_id, good in self.goods.items():
                    price_a = s_a.local_prices.get(good_id); price_b = s_b.local_prices.get(good_id)
                    if price_a is None or price_b is None or price_a <= 1e-6 or price_b <= 1e-6: continue

                    profit, seller, buyer, qty_avail = 0, None, None, 0.0; seller_price, buyer_price = 0.0, 0.0
                    if price_b > price_a * price_threshold: profit = price_b - price_a; seller, buyer = s_a, s_b; seller_price, buyer_price = price_a, price_b; qty_avail = seller.get_total_stored(good_id)
                    elif price_a > price_b * price_threshold: profit = price_a - price_b; seller, buyer = s_b, s_a; seller_price, buyer_price = price_b, price_a; qty_avail = seller.get_total_stored(good_id)

                    if seller is not None and qty_avail > 1e-6:
                        potential_qty = qty_avail
                        if not good.is_bulk and good_id in seller.item_storage: potential_qty = seller.item_storage[good_id][0].quantity if seller.item_storage[good_id] else 0
                        if potential_qty < min_trade_qty: potential_qty = 0 # Check against min trade qty
                        # Check if buyer can afford at least the minimum quantity
                        is_viable = (profit > 1e-6 and potential_qty >= min_trade_qty and buyer.wealth >= seller_price * min_trade_qty)
                        self.potential_trades_this_tick.append({'seller_id': seller.id, 'buyer_id': buyer.id, 'seller_name': seller.name, 'buyer_name': buyer.name, 'good_id': good.id, 'good_name': good.name, 'seller_price': seller_price, 'buyer_price': buyer_price, 'profit_per_unit': profit, 'qty_avail': qty_avail, 'potential_qty': potential_qty, 'is_viable_prelim': is_viable})
                        if is_viable: opportunities_for_execution.append({'from': seller, 'to': buyer, 'good': good, 'profit_per_unit': profit, 'potential_qty': potential_qty, 'seller_price': seller_price, 'buyer_price': buyer_price})

        opportunities_for_execution.sort(key=lambda x: x['profit_per_unit'], reverse=True)
        return opportunities_for_execution

    def execute_trades(self, opportunities):
        """Attempts to execute trades, checking per-settlement trade capacity."""
        trades_executed_log_entries = []; self.executed_trade_details_this_tick.clear(); self.failed_trades_this_tick.clear()
        trades_count_global = 0; max_trades_global = self.params.get('max_trades_per_tick', 200)
        min_trade_qty = self.params.get('min_trade_qty', 0.01) # Use config param
        log_max_len = self.params.get('world_trade_log_max_length', 10) # Use config param

        current_settlements_state = self.settlements.copy()

        for i, trade in enumerate(opportunities):
            seller_obj = current_settlements_state.get(trade['from'].id)
            buyer_obj = current_settlements_state.get(trade['to'].id)
            good = trade['good']
            profit = trade['profit_per_unit']; seller_potential_qty = trade['potential_qty']; seller_price = trade['seller_price']
            fail_reason = ""

            if not seller_obj or not buyer_obj or seller_obj.is_abandoned or buyer_obj.is_abandoned:
                 fail_reason = "Settlement abandoned/removed"; self.failed_trades_this_tick.append({'seller_id': trade['from'].id, 'buyer_id': trade['to'].id, 'good_id': good.id, 'fail_reason': fail_reason, 'tick': self.tick}); continue

            fail_log_base = {'seller_id': seller_obj.id, 'buyer_id': buyer_obj.id, 'seller_name': seller_obj.name, 'buyer_name': buyer_obj.name, 'good_id': good.id, 'good_name': good.name, 'seller_price': seller_price, 'buyer_price': trade['buyer_price'], 'profit_per_unit': profit, 'potential_qty': seller_potential_qty, 'qty_avail': seller_obj.get_total_stored(good.id)}

            if trades_count_global >= max_trades_global: fail_reason = "Skipped (Global Max Trades)"; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # Check Per-Settlement Trade Capacity
            if seller_obj.trades_executed_this_tick >= seller_obj.trade_capacity:
                fail_reason = f"Seller max trades ({seller_obj.trades_executed_this_tick}/{seller_obj.trade_capacity})"; seller_obj.failed_trades_max_capacity_counter += 1; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue
            if buyer_obj.trades_executed_this_tick >= buyer_obj.trade_capacity:
                fail_reason = f"Buyer max trades ({buyer_obj.trades_executed_this_tick}/{buyer_obj.trade_capacity})"; buyer_obj.failed_trades_max_capacity_counter += 1; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # Determine Actual Trade Quantity
            trade_qty = 0.0; item_to_trade_instance_id = None
            if good.is_bulk:
                max_affordable = float('inf'); 
                if seller_price > 1e-6: max_affordable = buyer_obj.wealth / seller_price
                buyer_storage = max(0.0, buyer_obj.storage_capacity - buyer_obj.get_current_storage_load())
                trade_qty = min(seller_potential_qty, max_affordable, buyer_storage)
            else:
                 if good.id in seller_obj.item_storage and seller_obj.item_storage[good.id]:
                    item = seller_obj.item_storage[good.id][0]; trade_qty = item.quantity; item_to_trade_instance_id = item.instance_id
                 else: fail_reason = "Seller Lacks Non-Bulk Item (Exec)"; self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # Ensure trade quantity meets minimum threshold from config
            if trade_qty < min_trade_qty:
                 if seller_potential_qty < min_trade_qty: fail_reason = "Seller stock too low"
                 elif 'max_affordable' in locals() and max_affordable < min_trade_qty: fail_reason = "Buyer cannot afford min qty"
                 elif 'buyer_storage' in locals() and buyer_storage < min_trade_qty: fail_reason = "Buyer storage too low for min qty"
                 else: fail_reason = f"Calc trade qty ({trade_qty:.3f}) too small"
                 self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason}); continue

            # Check Execution Feasibility
            transaction_cost = seller_price * trade_qty
            can_afford = buyer_obj.wealth >= (transaction_cost - 1e-6)
            has_stock = seller_obj.get_total_stored(good.id) >= (trade_qty - 1e-6)
            if not can_afford: fail_reason += f"Buyer Cannot Afford ({buyer_obj.wealth:.1f}<{transaction_cost:.1f}); "
            if not has_stock: fail_reason += f"Seller Lacks Stock ({seller_obj.get_total_stored(good.id):.1f}<{trade_qty:.1f}); "

            # Execute Transaction
            if can_afford and has_stock:
                removed_qty, consumed_instances = seller_obj.remove_from_storage(good.id, trade_qty, tick=self.tick)
                if removed_qty < trade_qty * 0.999:
                    fail_reason += f"Failed Stock Removal ({removed_qty:.1f}/{trade_qty:.1f})";
                    if consumed_instances: seller_obj.add_to_storage(good, item_instance=consumed_instances[0], tick=self.tick)
                    elif removed_qty > 1e-6: seller_obj.add_to_storage(good, quantity=removed_qty, tick=self.tick)
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()}); continue

                item_instance_for_buyer = None
                if not good.is_bulk and consumed_instances:
                    orig_part = consumed_instances[0]; item_instance_for_buyer = ItemInstance(good_id=good.id, origin_settlement_id=orig_part.origin_settlement_id, quantity=removed_qty, quality=orig_part.quality)
                    item_instance_for_buyer.trade_history = orig_part.trade_history[:]; item_instance_for_buyer.trade_history.append((seller_obj.id, seller_price, self.tick))
                    if item_to_trade_instance_id: item_instance_for_buyer.instance_id = item_to_trade_instance_id

                added_qty = buyer_obj.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_instance_for_buyer, tick=self.tick)

                if added_qty >= removed_qty * 0.999:
                    # --- Success! ---
                    final_cost = seller_price * added_qty; seller_obj.wealth += final_cost; buyer_obj.wealth -= final_cost
                    seller_obj.trades_executed_this_tick += 1; buyer_obj.trades_executed_this_tick += 1 # Increment counters
                    trade_log_msg = (f"T{self.tick}: {seller_obj.name} -> {buyer_obj.name}, {added_qty:.2f} {good.name} @ {seller_price:.2f}")
                    trades_executed_log_entries.append(trade_log_msg)
                    self.executed_trade_details_this_tick.append({'seller_id': seller_obj.id, 'buyer_id': buyer_obj.id, 'seller_name': seller_obj.name, 'buyer_name': buyer_obj.name, 'good_id': good.id, 'good_name': good.name, 'quantity': added_qty, 'seller_price': seller_price, 'buyer_price': trade['buyer_price'], 'profit_per_unit': profit, 'tick': self.tick})
                    trades_count_global += 1
                else: # Failed to add
                    fail_reason += f"Buyer Storage Failed (Avail: {max(0, buyer_obj.storage_capacity - buyer_obj.get_current_storage_load()):.1f})"
                    item_to_return = consumed_instances[0] if not good.is_bulk and consumed_instances else None
                    if item_to_return and item_to_return.trade_history: item_to_return.trade_history.pop()
                    seller_obj.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_to_return, tick=self.tick)
                    # seller_obj.add_log(f"Fail trade to {buyer_obj.name} (storage?), {removed_qty:.1f} {good.name} returned", self.tick) # Redundant?
                    # buyer_obj.add_log(f"Fail trade from {seller_obj.name} (storage full?)", self.tick) # Redundant?
                    self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})
            else: # Failed initial check
                self.failed_trades_this_tick.append({**fail_log_base, 'fail_reason': fail_reason.strip()})

        # Use config param for log length
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
            settlement.trades_executed_this_tick = 0 # Reset per-settlement counter
            settlement.production_this_tick.clear() # Clear production tracker

        # --- Get Current State ---
        current_settlements = list(self.settlements.values())
        active_settlements = [s for s in current_settlements if not s.is_abandoned]

        # --- Construction Progress Phase ---
        for settlement in active_settlements:
             settlement.progress_upgrade(self.tick, self.goods)

        # --- Core Economic Phases ---
        for settlement in active_settlements: settlement.produce(self.goods, self.tick)
        for settlement in active_settlements: settlement.consume(self.goods, self.tick)
        for settlement in active_settlements: settlement.update_prices(self.goods, self.tick)

        # --- Trade Phase ---
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
        for settlement in current_settlements:
            if settlement.is_abandoned: continue
            if settlement.wealth < abandonment_wealth_threshold: settlement.ticks_below_wealth_threshold += 1
            else: settlement.ticks_below_wealth_threshold = 0
            if settlement.ticks_below_wealth_threshold >= abandonment_ticks_threshold:
                settlement.is_abandoned = True; settlements_to_remove_ids.append(settlement.id)
                print(f"INFO: Settlement {settlement.name} ({settlement.id}) abandoned at tick {self.tick} (Low Wealth: {settlement.wealth:.0f}).")
                self.recent_trades_log.insert(0, f"T{self.tick}: {settlement.name} abandoned!"); self.recent_trades_log = self.recent_trades_log[:self.params.get('world_trade_log_max_length', 10)] # Use param
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
                    if emigrant.population <= 1 or emigrant.id not in self.settlements: continue
                    best_target = None; min_dist = float('inf')
                    for immigrant in potential_immigrants:
                        if emigrant.id == immigrant.id or immigrant.id not in self.settlements: continue
                        dist = self._calculate_distance(emigrant, immigrant)
                        if dist < min_dist: min_dist = dist; best_target = immigrant
                    if best_target:
                        num_to_migrate = max(1, int(emigrant.population * migration_max_percentage))
                        num_to_migrate = min(num_to_migrate, emigrant.population - 1)
                        if num_to_migrate > 0:
                            emigrant.population -= num_to_migrate; best_target.population += num_to_migrate
                            self.migration_details_this_tick.append({'tick': self.tick, 'from_id': emigrant.id, 'from_name': emigrant.name,'to_id': best_target.id, 'to_name': best_target.name, 'quantity': num_to_migrate})
                            emigrant.update_derived_stats(); best_target.update_derived_stats()
                            migrants_moved_total += num_to_migrate

# --- NO Main Execution Block Here ---
