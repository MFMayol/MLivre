from data_structures import Order, Runner
from collections import defaultdict
from typing import Dict, List
#from Solucion import Solucion


class Instance:
    """
    Representa una instancia completa del problema de optimización.

    Attributes:
        orders (List[Order]): Lista de órdenes.
        runners (List[Runner]): Lista de corredores.
        num_items (int): Número total de tipos de ítems disponibles.
        lb (int): Límite inferior de unidades para formar una wave.
        ub (int): Límite superior de unidades para formar una wave.
    """
    def __init__(self, orders: List[Order], runners: List[Runner], num_items: int, lb: int, ub: int):
        self.orders = orders
        self.runners = runners
        self.num_items = num_items
        self.lb = lb
        self.ub = ub

    def constructora(self):
        """
        Construye una solución factible a partir de una instancia del problema.

        Paso 1: Selecciona órdenes en orden decreciente de unidades hasta pasar el UB.
        Paso 2: Selecciona corredores también en orden decreciente de capacidad,
                hasta que se puede satisfacer toda la demanda de las órdenes seleccionadas.

        Args:
            None

        Returns:
            Solucion: Solución con las órdenes y corredores seleccionados.
        """
        LB = self.lb

        # Ordenar las órdenes por mayor cantidad total de unidades
        ordenes_ordenadas = sorted(self.orders, key=lambda o: o.total_units, reverse=True)
        ordenes_seleccionadas = []
        total_unidades = 0

        # Seleccionar órdenes hasta superar el Upper Bound
        for orden in ordenes_ordenadas:
            ordenes_seleccionadas.append(orden)
            total_unidades += orden.total_units
            if total_unidades + orden.total_units > LB:
                    break

        # Calcular demanda total de productos por ítem
        demanda_total = {i:0 for i in range(self.num_items)}
        for orden in ordenes_seleccionadas:
            for item, qty in orden.items.items():
                demanda_total[item] += qty

        # Ordenar corredores por mayor capacidad total
        corredores_ordenados = sorted(self.runners, key=lambda r: sum(r.stock.values()), reverse=True)
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

        return Solucion(selected_orders=ordenes_seleccionadas, selected_runners= corredores_seleccionados, instance= self)


class Solucion:
    """
    Clase que representa una solución al problema.

    Atributos:
        selected_orders (List[Order]): Lista de órdenes seleccionadas para la solución.
        selected_runners (List[Runner]): Lista de corredores seleccionados para abastecer la demanda.
        instance (Instance): Instancia del problema.
    """
    def __init__(self, selected_orders: List[Order], selected_runners: List[Runner], instance : Instance):
        self.selected_orders = selected_orders
        self.selected_runners = selected_runners
        self.instance = instance

    def total_units(self) -> int:
        """Retorna el total de unidades solicitadas por las órdenes seleccionadas."""
        return sum(order.total_units for order in self.selected_orders)

    def num_runners(self) -> int:
        """Retorna el número de corredores utilizados."""
        return len(self.selected_runners)

    def objective_value(self) -> float:
        """
        Retorna el valor objetivo de la solución: total de unidades / número de corredores.
        Si no hay corredores, retorna 0.
        """
        if self.num_runners() == 0:
            return 0
        return self.total_units() / self.num_runners()
    
    # creamos método para ver si es factible o no
    def is_factible(self) -> bool:
        """
        Descripción: Método que verifica si la solución es factible considerando que la demanda total de productos por ítem es mayor o igual que la cantidad de productos que se llevan en cada pasillo.
        Args:
            None
        Returns:
            bool: True si la solución es factible, False en caso contrario.
        """

        # primero guardamos en un diccionario la cantidad de productos solicitados en las ordenes seleccionadas inicializandolas con 0 
        demanda_total = { i:0 for i in range(self.instance.num_items)}
        
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total[item] = demanda_total.get(item, 0) + quantity

        # ahora vemos la cantidad de productos que se llevan de cada uno en todos los pasillos en un diccionario
        stock_total = { i:0 for i in range(self.instance.num_items)}
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_total[item] = stock_total.get(item, 0) + quantity

        # ahora vemos si la cantidad de productos solicitados en las ordenes seleccionadas es mayor o igual que la cantidad de productos que se llevan en cada pasillo
        return all(stock_total[i] >= demanda_total[i] for i in demanda_total)
    

    # ahora creamos el print para que se vea mejor
    def __str__(self):
        return f"Solución con {len(self.selected_orders)} órdenes y {len(self.selected_runners)} corredores con un ratio de {self.objective_value():.2f}"

