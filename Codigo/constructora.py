from data_structures import Order, Runner
from collections import defaultdict
from Instance import Instance, Solucion

def constructora(instance: Instance) -> Solucion:
    """
    Construye una solución factible a partir de una instancia del problema.

    Paso 1: Selecciona órdenes en orden decreciente de unidades hasta pasar el UB.
    Paso 2: Selecciona corredores también en orden decreciente de capacidad,
            hasta que se puede satisfacer toda la demanda de las órdenes seleccionadas.

    Args:
        instance (Instance): Instancia del problema.

    Returns:
        Solucion: Solución con las órdenes y corredores seleccionados.
    """
    LB = instance.ub

    # Ordenar las órdenes por mayor cantidad total de unidades
    ordenes_ordenadas = sorted(instance.orders, key=lambda o: o.total_units, reverse=True)
    ordenes_seleccionadas = []
    total_unidades = 0

    # Seleccionar órdenes hasta superar el Upper Bound
    for orden in ordenes_ordenadas:
        ordenes_seleccionadas.append(orden)
        total_unidades += orden.total_units
        if total_unidades + orden.total_units > LB:
                break

    # Calcular demanda total de productos por ítem
    demanda_total = {i:0 for i in range(instance.num_items)}
    for orden in ordenes_seleccionadas:
        for item, qty in orden.items.items():
            demanda_total[item] += qty

    # Ordenar corredores por mayor capacidad total
    corredores_ordenados = sorted(instance.runners, key=lambda r: sum(r.stock.values()), reverse=True)
    corredores_seleccionados = []
    stock_disponible = defaultdict(int)

    for corredor in corredores_ordenados:
        for item, qty in corredor.stock.items():
            stock_disponible[item] += qty
        corredores_seleccionados.append(corredor)

        # Verificar si el stock ya cubre toda la demanda
        cubre_demanda = all(stock_disponible[i] >= demanda_total[i] for i in demanda_total)
        if cubre_demanda:
            break

    return Solucion(selected_orders= ordenes_seleccionadas, selected_runners= corredores_seleccionados, instance= instance)
