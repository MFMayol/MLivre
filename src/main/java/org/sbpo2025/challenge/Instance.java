from typing import List, Dict
from data_structures import Order, Runner # Asumiendo que Order y Runner están en data_structures.py

class Instance:
    def __init__(self, orders: List[Order], runners: List[Runner], num_items: int, lb: int, ub: int):
        self.orders = orders
        self.runners = runners
        self.num_items = num_items
        self.lb = lb
        self.ub = ub

    def get_order_by_index(self, index: int) -> Order:
        # Implementación simple, asumiendo que los índices son secuenciales y válidos
        if 0 <= index < len(self.orders):
            return self.orders[index]
        raise IndexError(f"Order index {index} out of bounds.")

    def get_runner_by_index(self, index: int) -> Runner:
        # Implementación simple, asumiendo que los índices son secuenciales y válidos
        if 0 <= index < len(self.runners):
            return self.runners[index]
        raise IndexError(f"Runner index {index} out of bounds.")

    def __repr__(self):
        return (f"Instance(orders={len(self.orders)}, runners={len(self.runners)}, "
                f"num_items={self.num_items}, lb={self.lb}, ub={self.ub})")
