import random
import uuid
import math
import os
import time
from collections import defaultdict, OrderedDict
import json

# --- Data Structures ---

class Good:
    """Represents a type of tradable good, potentially with a production recipe."""
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
    """Represents a specific instance or batch of a non-bulk good."""
    def __init__(self, good_id, origin_settlement_id, quantity=1, quality=1.0):
        self.instance_id = str(uuid.uuid4()); self.good_id = good_id
        self.origin_settlement_id = origin_settlement_id; self.current_location_settlement_id = origin_settlement_id
        self.quantity = quantity; self.quality = quality; self.trade_history = []
    def __repr__(self):
        history_summary = f", History: {len(self.trade_history)} steps" if self.trade_history else ""
        return (f"Item(ID: {self.instance_id[:4]}..., Good: {self.good_id}, "
                f"Origin: {self.origin_settlement_id}, Loc: {self.current_location_settlement_id}, "
                f"Qty: {self.quantity:.1f}{history_summary})")

class Settlement:
    """Represents a settlement, the core economic unit."""
    def __init__(self, id, name, region_id, population, terrain_type,
                 storage_capacity_per_pop, labor_per_pop, default_initial_wealth,
                 city_population_threshold, city_storage_multiplier, # <<< Added params
                 initial_wealth=None, x=0, y=0):
        self.id = id; self.name = name; self.region_id = region_id
        self.population = population; self.terrain_type = terrain_type
        self.x = x; self.y = y
        self.bulk_storage = defaultdict(float); self.item_storage = defaultdict(list)

        # <<< Calculate storage capacity based on city status AT CREATION >>>
        base_capacity = population * storage_capacity_per_pop
        if population >= city_population_threshold:
            self.storage_capacity = base_capacity * city_storage_multiplier
            # print(f"DEBUG: {name} is a city (Pop {population}), Storage: {self.storage_capacity}") # Optional Debug
        else:
            self.storage_capacity = base_capacity
            # print(f"DEBUG: {name} is not a city (Pop {population}), Storage: {self.storage_capacity}") # Optional Debug

        self.max_labor_pool = self.population * labor_per_pop
        self.current_labor_pool = self.max_labor_pool
        self.consumption_needs = defaultdict(lambda: 1.0); self.local_prices = {}
        self.wealth = initial_wealth if initial_wealth is not None else default_initial_wealth
        self.market_level = 1; self.log = []

    def __repr__(self): return f"Settlement({self.name}, Pop: {self.population}, Wealth: {self.wealth:.0f}, Terrain: {self.terrain_type}, Pos:({self.x},{self.y}))"
    def add_log(self, message, tick): self.log.append(f"T{tick}: {message}"); self.log = self.log[-10:]
    def get_total_stored(self, good_id): return self.bulk_storage.get(good_id, 0) + sum(item.quantity for item in self.item_storage.get(good_id, []))
    def get_current_storage_load(self): return sum(self.bulk_storage.values()) + sum(item.quantity for items in self.item_storage.values() for item in items)

    def add_to_storage(self, good, quantity=None, item_instance=None, tick=0):
        current_load = self.get_current_storage_load()
        available_capacity = max(0, self.storage_capacity - current_load)
        added_qty = 0
        if available_capacity <= 1e-6: return 0
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
        removed_qty = 0; consumed_instances = []
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

    def produce(self, all_goods_dict, max_production_passes, world_tick):
        self.current_labor_pool = self.max_labor_pool
        for _pass in range(max_production_passes):
            production_possible_in_pass = False
            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            if not producible_goods: break
            producible_items = list(producible_goods.items())
            random.shuffle(producible_items)
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
                temp_storage_state = {}; temp_output_storage_state = {}
                self.current_labor_pool -= recipe['labor']; self.wealth -= recipe['wealth_cost']
                inputs_consumed_successfully = True
                if required_inputs:
                    for input_good_id, input_qty in required_inputs.items():
                        temp_storage_state[input_good_id] = self.get_total_stored(input_good_id)
                        removed_qty, _ = self.remove_from_storage(input_good_id, input_qty, tick=world_tick)
                        if removed_qty < input_qty * 0.99:
                            inputs_consumed_successfully = False
                            self.current_labor_pool = original_labor; self.wealth = original_wealth
                            for gid, initial_qty in temp_storage_state.items():
                                current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                                if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                            break
                    if not inputs_consumed_successfully: continue
                outputs_produced_successfully = True
                for output_good_id, output_qty in recipe['outputs'].items():
                    output_good = all_goods_dict[output_good_id]
                    temp_output_storage_state[output_good_id] = self.get_total_stored(output_good_id)
                    added_qty = self.add_to_storage(output_good, quantity=output_qty, tick=world_tick)
                    if added_qty < output_qty * 0.99:
                        outputs_produced_successfully = False
                        self.current_labor_pool = original_labor; self.wealth = original_wealth
                        for gid, initial_qty in temp_storage_state.items():
                             current_qty = self.get_total_stored(gid); qty_to_add_back = initial_qty - current_qty
                             if qty_to_add_back > 1e-6: self.add_to_storage(all_goods_dict[gid], quantity=qty_to_add_back)
                        for gid, initial_qty in temp_output_storage_state.items():
                            current_qty = self.get_total_stored(gid); qty_to_remove = current_qty - initial_qty
                            if qty_to_remove > 1e-6: self.remove_from_storage(gid, qty_to_remove)
                        break
                if not outputs_produced_successfully: continue
                production_possible_in_pass = True
            if not production_possible_in_pass: break

    def consume(self, goods_dict, params, world_tick):
        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            if good_id in ['iron_ore', 'seed']: continue
            # Determine if this good should be consumed here
            consume_this = False
            if good_id == 'bread' and is_city: consume_this = True
            elif good_id != 'bread' and not (good_id == 'grain' and is_city): consume_this = True # Non-cities consume non-bread (incl grain), cities consume non-bread/non-grain

            if consume_this:
                demand_modifier = self.consumption_needs[good_id]
                amount_needed = (base_consumption_rate * self.population * demand_modifier * (1 + random.uniform(-0.1, 0.1)))
                amount_needed = max(0, amount_needed)
                if amount_needed > 0.01:
                    available = self.get_total_stored(good_id)
                    amount_to_consume = min(amount_needed, available)
                    if amount_to_consume > 0.01:
                        removed_qty, _ = self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)

    def update_prices(self, goods_dict, params, world_tick):
        base_consumption_rate = params.get('base_consumption_rate', 0.1)
        price_sensitivity = params.get('price_sensitivity', 2.0)
        min_price_multiplier = params.get('min_price_multiplier', 0.1)
        max_price_multiplier = params.get('max_price_multiplier', 10.0)
        city_pop_threshold = params.get('city_population_threshold', 150)
        is_city = self.population >= city_pop_threshold

        for good_id, good in goods_dict.items():
            supply = self.get_total_stored(good_id); demand_estimate = 0.01
            if good_id not in ['iron_ore', 'seed']:
                 if good_id == 'bread' and is_city: demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
                 elif good_id != 'bread' and not (good_id == 'grain' and is_city): demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
            supply = max(supply, 0.01); demand_estimate = max(demand_estimate, 0.01); ratio = supply / demand_estimate
            price_modifier = math.pow(ratio, -price_sensitivity)
            min_price = good.base_value * min_price_multiplier
            max_price = good.base_value * max_price_multiplier
            new_price = good.base_value * price_modifier; self.local_prices[good_id] = max(min_price, min(new_price, max_price))

class Region:
    def __init__(self, id, name, resource_modifiers=None): self.id = id; self.name = name; self.resource_modifiers = resource_modifiers if resource_modifiers else {}; self.settlements = []
    def add_settlement(self, settlement): self.settlements.append(settlement)
class Civilization:
    def __init__(self, id, name): self.id = id; self.name = name; self.regions = []
    def add_region(self, region): self.regions.append(region)

class World:
    def __init__(self, sim_params):
        self.tick = 0; self.goods = OrderedDict(); self.settlements = OrderedDict(); self.regions = OrderedDict(); self.civilizations = OrderedDict(); self.trade_routes = {}
        self.recent_trades_log = []; self.executed_trade_details_this_tick = []
        self.params = sim_params
        print(f"World initialized with parameters: {self.params}")

    def add_good(self, good): self.goods[good.id] = good
    def add_settlement(self, settlement): self.settlements[settlement.id] = settlement
    def add_region(self, region): self.regions[region.id] = region
    def add_civilization(self, civilization): self.civilizations[civilization.id] = civilization
    def get_all_settlements(self): return list(self.settlements.values())

    def find_trade_opportunities(self):
        opportunities = []
        all_settlements = self.get_all_settlements()
        price_threshold_multiplier = self.params.get('trade_profit_margin_threshold', 1.05)
        for i in range(len(all_settlements)):
            for j in range(i + 1, len(all_settlements)):
                settlement_a, settlement_b = all_settlements[i], all_settlements[j]
                for good_id, good in self.goods.items():
                    price_a = settlement_a.local_prices.get(good_id); price_b = settlement_b.local_prices.get(good_id)
                    if price_a is None or price_b is None: continue
                    profit, seller, buyer, qty_avail = 0, None, None, 0
                    seller_price, buyer_price = 0, 0
                    if price_b > price_a * price_threshold_multiplier:
                        profit = price_b - price_a; seller, buyer = settlement_a, settlement_b
                        seller_price, buyer_price = price_a, price_b
                        qty_avail = settlement_a.get_total_stored(good_id)
                    elif price_a > price_b * price_threshold_multiplier:
                        profit = price_a - price_b; seller, buyer = settlement_b, settlement_a
                        seller_price, buyer_price = price_b, price_a
                        qty_avail = settlement_b.get_total_stored(good_id)
                    if profit > 1e-6 and qty_avail > 1e-6 and buyer.wealth > 0:
                        potential_trade_qty = 1.0
                        if not good.is_bulk and good_id in seller.item_storage:
                            items = seller.item_storage[good_id]
                            potential_trade_qty = min(item.quantity for item in items) if items else 0
                        potential_trade_qty = min(potential_trade_qty, qty_avail)
                        if potential_trade_qty > 1e-6:
                            opportunities.append({'from': seller, 'to': buyer, 'good': good, 'profit_per_unit': profit, 'potential_qty': potential_trade_qty, 'seller_price': seller_price, 'buyer_price': buyer_price})
        opportunities.sort(key=lambda x: x['profit_per_unit'], reverse=True);
        return opportunities

    def execute_trades(self, opportunities):
        trades_executed_log_entries = []
        self.executed_trade_details_this_tick.clear()
        trades_count = 0
        max_trades = self.params.get('max_trades_per_tick', 5)
        for trade in opportunities:
            if trades_count >= max_trades: break
            seller, buyer, good = trade['from'], trade['to'], trade['good']
            profit, potential_qty = trade['profit_per_unit'], trade['potential_qty']
            seller_price = trade['seller_price']
            trade_qty = min(potential_qty, 1.0)
            item_to_trade_instance_id = None
            if not good.is_bulk:
                 if good.id in seller.item_storage and seller.item_storage[good.id]:
                    item_to_trade = seller.item_storage[good.id][0]
                    trade_qty = item_to_trade.quantity
                    item_to_trade_instance_id = item_to_trade.instance_id
                 else: continue
            trade_qty = max(0.01, trade_qty)
            transaction_price = seller_price
            transaction_cost = transaction_price * trade_qty
            can_afford = buyer.wealth >= transaction_cost
            has_stock = seller.get_total_stored(good.id) >= trade_qty
            if can_afford and has_stock:
                removed_qty, consumed_instances = seller.remove_from_storage(good.id, trade_qty, tick=self.tick)
                item_instance_for_buyer = None
                if removed_qty < trade_qty * 0.99: continue
                if not good.is_bulk and consumed_instances:
                    original_instance_part = consumed_instances[0]
                    item_instance_for_buyer = ItemInstance(good_id=good.id, origin_settlement_id=original_instance_part.origin_settlement_id, quantity=removed_qty, quality=original_instance_part.quality)
                    item_instance_for_buyer.trade_history = original_instance_part.trade_history[:]
                    item_instance_for_buyer.trade_history.append((seller.id, transaction_price, self.tick))
                    if item_to_trade_instance_id: item_instance_for_buyer.instance_id = item_to_trade_instance_id
                added_qty = buyer.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_instance_for_buyer, tick=self.tick)
                if added_qty >= removed_qty * 0.99:
                    final_cost = transaction_price * added_qty
                    seller.wealth += final_cost; buyer.wealth -= final_cost
                    trade_log_msg = (f"T{self.tick}: {seller.name} -> {buyer.name}, {added_qty:.2f} {good.name} @ {transaction_price:.2f}")
                    trades_executed_log_entries.append(trade_log_msg)
                    self.executed_trade_details_this_tick.append({'seller_id': seller.id, 'buyer_id': buyer.id, 'seller_name': seller.name, 'buyer_name': buyer.name, 'good_id': good.id, 'good_name': good.name, 'quantity': added_qty, 'seller_price': seller_price, 'buyer_price': trade['buyer_price'], 'profit_per_unit': profit, 'tick': self.tick})
                    trades_count += 1
                else: # Failed storage at buyer
                    item_to_return = None
                    if not good.is_bulk and consumed_instances:
                         item_to_return = consumed_instances[0]
                         if item_to_return.trade_history: item_to_return.trade_history.pop()
                    seller.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_to_return, tick=self.tick)
                    seller.add_log(f"Fail trade to {buyer.name} (storage?), {removed_qty:.1f} {good.name} returned", self.tick)
                    buyer.add_log(f"Fail trade from {seller.name} (storage full?)", self.tick)
        self.recent_trades_log = trades_executed_log_entries + self.recent_trades_log
        self.recent_trades_log = self.recent_trades_log[:10]

    def simulation_step(self):
        """Executes one full tick of the simulation using configured parameters."""
        self.tick += 1
        all_settlements = self.get_all_settlements()
        max_prod_passes = self.params.get('max_production_passes', 5)

        # Production Phase
        for settlement in all_settlements:
            settlement.produce(self.goods, max_prod_passes, self.tick)

        # Consumption Phase
        for settlement in all_settlements:
            settlement.consume(self.goods, self.params, self.tick) # Pass full params

        # Price Update Phase
        for settlement in all_settlements:
            settlement.update_prices(self.goods, self.params, self.tick) # Pass full params

        # Trade Execution Phase
        opportunities = self.find_trade_opportunities() # Uses threshold from self.params
        if opportunities:
            self.execute_trades(opportunities) # Uses max_trades from self.params

        # <<< NEW: Upkeep Phase >>>
        storage_cost_rate = self.params.get('storage_cost_per_unit', 0.0)
        if storage_cost_rate > 0:
            # print(f"--- T{self.tick}: Upkeep Phase ---") # Optional debug
            for settlement in all_settlements:
                total_stored = settlement.get_current_storage_load()
                storage_upkeep = total_stored * storage_cost_rate
                if storage_upkeep > 0:
                    settlement.wealth -= storage_upkeep
                    # print(f"  {settlement.name}: Stored {total_stored:.1f}, Upkeep Cost {storage_upkeep:.2f}, New Wealth {settlement.wealth:.0f}") # Optional debug


# --- NO Main Execution Block Here ---
