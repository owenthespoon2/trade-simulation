import random
import uuid
import math
import os # Keep os for potential future use (e.g., path joining)
import time # Keep time for potential future use (e.g., performance timing)
from collections import defaultdict, OrderedDict
import json # Keep json if needed for other logic, or remove if only for setup

# --- Constants (Logic-related) ---
PRICE_SENSITIVITY = 2.0
# INITIAL_WEALTH = 500 # Defined here, but can be overridden in setup
STORAGE_CAPACITY_PER_POP = 10
MAX_TRADES_PER_TICK = 5 # Related to trade execution logic
LABOR_PER_POP = 0.5 # Related to production logic

# --- Data Structures ---

class Good:
    """Represents a type of tradable good, potentially with a production recipe."""
    def __init__(self, id, name, base_value, is_bulk=True, is_producible=False):
        self.id = id; self.name = name; self.base_value = base_value
        self.is_bulk = is_bulk; self.is_producible = is_producible
        self.recipe = None
    def __repr__(self): return f"Good({self.name})"
    def add_recipe(self, inputs, outputs, labor, required_terrain=None, wealth_cost=0):
        """Adds a production recipe to this good (loaded from config)."""
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
    """Represents a settlement, the core economic unit, now with terrain and labor."""
    # Use a class attribute for default, allow override in init/setup
    DEFAULT_INITIAL_WEALTH = 500

    def __init__(self, id, name, region_id, population, terrain_type, initial_wealth=None): # Allow overriding initial wealth
        self.id = id; self.name = name; self.region_id = region_id
        self.population = population; self.terrain_type = terrain_type
        self.bulk_storage = defaultdict(float); self.item_storage = defaultdict(list)
        self.storage_capacity = population * STORAGE_CAPACITY_PER_POP
        self.consumption_needs = defaultdict(lambda: 1.0); self.local_prices = {}
        # Set initial wealth: use provided value or default
        self.wealth = initial_wealth if initial_wealth is not None else self.DEFAULT_INITIAL_WEALTH
        self.market_level = 1; self.log = []
        self.max_labor_pool = self.population * LABOR_PER_POP
        self.current_labor_pool = self.max_labor_pool # Start with full labor pool
    def __repr__(self): return f"Settlement({self.name}, Pop: {self.population}, Wealth: {self.wealth:.0f}, Terrain: {self.terrain_type})"
    def add_log(self, message, tick): self.log.append(f"T{tick}: {message}"); self.log = self.log[-10:] # Keep last 10 logs
    def get_total_stored(self, good_id): return self.bulk_storage.get(good_id, 0) + sum(item.quantity for item in self.item_storage.get(good_id, []))
    def get_current_storage_load(self): return sum(self.bulk_storage.values()) + sum(item.quantity for items in self.item_storage.values() for item in items)
    def add_to_storage(self, good, quantity=None, item_instance=None, tick=0):
        current_load = self.get_current_storage_load(); available_capacity = max(0, self.storage_capacity - current_load)
        if available_capacity <= 1e-6: return 0
        if item_instance:
            needed_capacity = item_instance.quantity
            if needed_capacity <= available_capacity: self.item_storage[item_instance.good_id].append(item_instance); item_instance.current_location_settlement_id = self.id; return item_instance.quantity
            else: return 0
        elif good and quantity is not None:
            amount_to_add = min(quantity, available_capacity)
            if amount_to_add <= 1e-6: return 0
            if good.is_bulk: self.bulk_storage[good.id] += amount_to_add
            else: new_item = ItemInstance(good.id, self.id, quantity=amount_to_add); self.item_storage[good.id].append(new_item)
            return amount_to_add
        return 0
    def remove_from_storage(self, good_id, quantity, tick=0):
        removed_qty = 0; consumed_instances = []
        if good_id in self.bulk_storage:
            take_from_bulk = min(quantity, self.bulk_storage[good_id]); self.bulk_storage[good_id] -= take_from_bulk; removed_qty += take_from_bulk
            if self.bulk_storage[good_id] < 1e-6: del self.bulk_storage[good_id]
        remaining_needed = quantity - removed_qty
        if remaining_needed > 1e-6 and good_id in self.item_storage:
            items_list = self.item_storage[good_id]; indices_to_remove = []
            # Simple FIFO for now (process list in order)
            for i, item in enumerate(items_list):
                if remaining_needed <= 1e-6: break
                take_from_item = min(remaining_needed, item.quantity)
                consumed_instance_part = ItemInstance(good_id=item.good_id, origin_settlement_id=item.origin_settlement_id, quantity=take_from_item, quality=item.quality)
                consumed_instance_part.instance_id = item.instance_id; consumed_instance_part.trade_history = item.trade_history[:]
                consumed_instances.append(consumed_instance_part); item.quantity -= take_from_item; removed_qty += take_from_item; remaining_needed -= take_from_item
                if item.quantity < 1e-6: indices_to_remove.append(i)
            for i in sorted(indices_to_remove, reverse=True): del items_list[i]
            if not self.item_storage[good_id]: del self.item_storage[good_id]
        return removed_qty, consumed_instances
    def produce(self, all_goods_dict, world_tick):
        """Core production logic based on recipes, labor, and inputs."""
        self.current_labor_pool = self.max_labor_pool # Replenish labor at start of production phase
        production_possible_in_pass = True
        while production_possible_in_pass:
            production_possible_in_pass = False
            producible_goods = OrderedDict((gid, g) for gid, g in all_goods_dict.items() if g.is_producible and g.recipe)
            for good_id, good in producible_goods.items():
                recipe = good.recipe
                while True: # Keep trying this recipe if possible
                    if recipe['required_terrain'] and self.terrain_type not in recipe['required_terrain']: break
                    if self.current_labor_pool < recipe['labor']: break
                    if self.wealth < recipe['wealth_cost']: break
                    inputs_available = True; required_inputs = recipe['inputs']
                    if required_inputs:
                        for input_good_id, input_qty in required_inputs.items():
                            if self.get_total_stored(input_good_id) < input_qty: inputs_available = False; break
                        if not inputs_available: break
                    self.current_labor_pool -= recipe['labor']; self.wealth -= recipe['wealth_cost']
                    inputs_consumed_successfully = True; consumed_input_details = {}
                    if required_inputs:
                        for input_good_id, input_qty in required_inputs.items():
                            removed_qty, _ = self.remove_from_storage(input_good_id, input_qty, tick=world_tick)
                            if removed_qty < input_qty * 0.99:
                                print(f"CRITICAL FAIL: {self.name} could not remove {input_good_id} for {good.name}"); inputs_consumed_successfully = False
                                self.current_labor_pool += recipe['labor']; self.wealth += recipe['wealth_cost'] # Rollback
                                for gid, qty in consumed_input_details.items(): self.add_to_storage(all_goods_dict[gid], quantity=qty)
                                break
                            consumed_input_details[input_good_id] = removed_qty
                    if not inputs_consumed_successfully: break
                    outputs_produced_successfully = True; produced_output_details = {}
                    for output_good_id, output_qty in recipe['outputs'].items():
                        output_good = all_goods_dict[output_good_id]
                        added_qty = self.add_to_storage(output_good, quantity=output_qty, tick=world_tick)
                        if added_qty < output_qty * 0.99:
                            print(f"WARN: {self.name} failed to store output {output_good_id} for {good.name}"); outputs_produced_successfully = False
                            self.current_labor_pool += recipe['labor']; self.wealth += recipe['wealth_cost'] # Rollback
                            for gid, qty in consumed_input_details.items(): self.add_to_storage(all_goods_dict[gid], quantity=qty)
                            for gid, qty in produced_output_details.items(): self.remove_from_storage(gid, qty)
                            break
                        produced_output_details[output_good_id] = added_qty
                    if not outputs_produced_successfully: break
                    if outputs_produced_successfully: production_possible_in_pass = True
    def consume(self, goods_dict, world_tick):
        """Core consumption logic."""
        base_consumption_rate = 0.1 # Could be a constant or settlement property
        for good_id, good in goods_dict.items():
            # Simple heuristic: don't consume raw industrial inputs via population need
            if good_id in ['iron_ore', 'seed']: continue
            demand_modifier = self.consumption_needs[good_id]; amount_needed = (base_consumption_rate * self.population * demand_modifier * (1 + random.uniform(-0.1, 0.1)))
            amount_needed = max(0, amount_needed)
            if amount_needed > 0.1:
                available = self.get_total_stored(good_id); amount_to_consume = min(amount_needed, available)
                if amount_to_consume > 0: removed_qty, _ = self.remove_from_storage(good_id, amount_to_consume, tick=world_tick)
    def update_prices(self, goods_dict, world_tick):
        """Core price update logic."""
        base_consumption_rate = 0.1
        for good_id, good in goods_dict.items():
            supply = self.get_total_stored(good_id); demand_estimate = 0.01
            # Estimate demand based on population for non-industrial goods
            if good_id not in ['iron_ore', 'seed']: demand_estimate = (base_consumption_rate * self.population * self.consumption_needs[good_id])
            supply = max(supply, 0.01); demand_estimate = max(demand_estimate, 0.01); ratio = supply / demand_estimate
            price_modifier = math.pow(ratio, -PRICE_SENSITIVITY); min_price = good.base_value * 0.1; max_price = good.base_value * 10.0
            new_price = good.base_value * price_modifier; self.local_prices[good_id] = max(min_price, min(new_price, max_price))

class Region:
    """Represents a geographical region."""
    def __init__(self, id, name, resource_modifiers=None): self.id = id; self.name = name; self.resource_modifiers = resource_modifiers if resource_modifiers else {}; self.settlements = []
    def add_settlement(self, settlement): self.settlements.append(settlement)
class Civilization:
    """Represents a group of regions (placeholder)."""
    def __init__(self, id, name): self.id = id; self.name = name; self.regions = []
    def add_region(self, region): self.regions.append(region)
class World:
    """Container for the entire simulation state and core simulation step."""
    def __init__(self): self.tick = 0; self.goods = OrderedDict(); self.settlements = OrderedDict(); self.regions = OrderedDict(); self.civilizations = OrderedDict(); self.trade_routes = {}; self.recent_trades = []
    def add_good(self, good): self.goods[good.id] = good
    def add_settlement(self, settlement): self.settlements[settlement.id] = settlement
    def add_region(self, region): self.regions[region.id] = region
    def add_civilization(self, civilization): self.civilizations[civilization.id] = civilization
    def get_all_settlements(self): return list(self.settlements.values())
    def find_trade_opportunities(self):
        """Core logic to find potential trades based on price differences."""
        opportunities = []
        all_settlements = self.get_all_settlements()
        # Use indices to avoid comparing pairs twice
        for i in range(len(all_settlements)):
            for j in range(i + 1, len(all_settlements)):
                settlement_a, settlement_b = all_settlements[i], all_settlements[j]
                for good_id, good in self.goods.items():
                    price_a = settlement_a.local_prices.get(good_id); price_b = settlement_b.local_prices.get(good_id)
                    if price_a is None or price_b is None: continue
                    profit, seller, buyer, qty_avail = 0, None, None, 0
                    # Determine potential seller/buyer based on price difference
                    if price_b > price_a: profit, seller, buyer, qty_avail = price_b - price_a, settlement_a, settlement_b, settlement_a.get_total_stored(good_id)
                    elif price_a > price_b: profit, seller, buyer, qty_avail = price_a - price_b, settlement_b, settlement_a, settlement_b.get_total_stored(good_id)
                    # Check basic viability
                    if profit > 1e-6 and qty_avail > 1e-6 and buyer.wealth > 0:
                        potential_trade_qty = 1.0 # Default for bulk
                        if not good.is_bulk and good_id in seller.item_storage: items = seller.item_storage[good_id]; potential_trade_qty = min(item.quantity for item in items) if items else 0
                        potential_trade_qty = min(potential_trade_qty, qty_avail) # Cannot trade more than available
                        if potential_trade_qty > 1e-6: opportunities.append({'from': seller, 'to': buyer, 'good': good, 'profit_per_unit': profit, 'potential_qty': potential_trade_qty})
        opportunities.sort(key=lambda x: x['profit_per_unit'], reverse=True); return opportunities
    def execute_trades(self, opportunities, max_trades):
        """Core logic to execute the most profitable trades."""
        trades_executed_this_tick = []; trades_count = 0
        for trade in opportunities:
            if trades_count >= max_trades: break
            seller, buyer, good = trade['from'], trade['to'], trade['good']; profit, potential_qty = trade['profit_per_unit'], trade['potential_qty']
            trade_qty = min(potential_qty, 1.0) # Attempt small trades
            # Refine quantity for non-bulk items based on smallest batch available
            if not good.is_bulk:
                 if good.id in seller.item_storage and seller.item_storage[good.id]:
                    try: item_to_trade = next(item for item in seller.item_storage[good.id] if abs(item.quantity - potential_qty) < 1e-6); trade_qty = min(trade_qty, item_to_trade.quantity)
                    except StopIteration: trade_qty = min(trade_qty, min(item.quantity for item in seller.item_storage[good.id]))
                 else: continue # No items left
            trade_qty = max(0.01, trade_qty); sell_price = seller.local_prices.get(good.id)
            if sell_price is None: continue
            transaction_price = sell_price * trade_qty
            # Final check for affordability and availability
            if buyer.wealth >= transaction_price and seller.get_total_stored(good.id) >= trade_qty:
                removed_qty, consumed_instances = seller.remove_from_storage(good.id, trade_qty, tick=self.tick); item_instance_for_buyer = None
                # Create ItemInstance for buyer if non-bulk
                if not good.is_bulk and consumed_instances:
                    original_instance_part = consumed_instances[0]
                    item_instance_for_buyer = ItemInstance(good_id=good.id, origin_settlement_id=original_instance_part.origin_settlement_id, quantity=removed_qty, quality=original_instance_part.quality)
                    item_instance_for_buyer.trade_history = original_instance_part.trade_history[:]; item_instance_for_buyer.trade_history.append((seller.id, sell_price, self.tick))
                # Add to buyer storage
                added_qty = buyer.add_to_storage(good, quantity=removed_qty if good.is_bulk else None, item_instance=item_instance_for_buyer, tick=self.tick)
                # Finalize if storage successful
                if added_qty >= removed_qty * 0.99:
                    final_price = sell_price * added_qty; seller.wealth += final_price; buyer.wealth -= final_price
                    trade_log_msg = (f"T{self.tick}: {seller.name} -> {buyer.name}, {added_qty:.2f} {good.name} @ {sell_price:.2f}")
                    trades_executed_this_tick.append(trade_log_msg); trades_count += 1
                else: # Log failed trade (e.g., buyer storage full)
                    seller.add_log(f"Fail trade to {buyer.name} (storage?), {removed_qty:.1f} {good.name} lost", self.tick); buyer.add_log(f"Fail trade from {seller.name} (storage?)", self.tick)
        # Update recent trades log
        self.recent_trades = trades_executed_this_tick + self.recent_trades; self.recent_trades = self.recent_trades[:10] # Keep last 10
    def simulation_step(self):
        """Executes one full tick of the simulation for all settlements."""
        self.tick += 1
        all_settlements = self.get_all_settlements()
        # --- Order of operations within a tick ---
        # 1. Production (consumes labor for the tick)
        for settlement in all_settlements:
            settlement.produce(self.goods, self.tick)
        # 2. Consumption (population needs)
        for settlement in all_settlements:
            settlement.consume(self.goods, self.tick)
        # 3. Price Update (based on new inventory levels)
        for settlement in all_settlements:
            settlement.update_prices(self.goods, self.tick)
        # 4. Trade Execution (based on new prices)
        opportunities = self.find_trade_opportunities()
        if opportunities:
            self.execute_trades(opportunities, max_trades=MAX_TRADES_PER_TICK)
        # 5. (Optional) End-of-tick updates / logging

# --- NO Main Execution Block Here ---
# This file now only contains definitions and logic.
# World setup and execution loop are handled elsewhere (e.g., world_setup.py, trade_ui.py).

