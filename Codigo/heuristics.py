from typing import List, Tuple
from collections import defaultdict
from data_structures import Instance, Order, Runner

def greedy_wave_selection(instance: Instance) -> Tuple[List[Order], List[Runner]]:
    """
    Heurística golosa que selecciona órdenes con la mayor cantidad de unidades posibles
    sin superar el límite superior de la wave. Luego selecciona corredores que puedan
    cumplir con la demanda total de los ítems requeridos.

    Args:
        instance (Instance): Instancia del problema que contiene órdenes, corredores y límites.

    Returns:
        Tuple[List[Order], List[Runner]]:
            - Lista de órdenes seleccionadas.
            - Lista de corredores necesarios para cumplir las órdenes.
            Si no es posible cumplir con la demanda mínima, se retorna ([], []).
    """
    selected_orders: List[Order] = []
    total_units = 0

    sorted_orders = sorted(instance.orders, key=lambda o: o.total_units(), reverse=True)

    for order in sorted_orders:
        if total_units + order.total_units() <= instance.ub:
            selected_orders.append(order)
            total_units += order.total_units()

    if total_units < instance.lb:
        return [], []

    remaining_needs = defaultdict(int)
    for order in selected_orders:
        for item, qty in order.items.items():
            remaining_needs[item] += qty

    used_runners = set()
    for runner in instance.runners:
        contribution = False
        for item, available in runner.stock.items():
            if remaining_needs[item] > 0:
                used = min(remaining_needs[item], available)
                remaining_needs[item] -= used
                if used > 0:
                    contribution = True
        if contribution:
            used_runners.add(runner)

        if all(v <= 0 for v in remaining_needs.values()):
            break

    if any(v > 0 for v in remaining_needs.values()):
        return [], []

    return selected_orders, list(used_runners)
