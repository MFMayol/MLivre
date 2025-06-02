from data_structures import Order, Runner
from Instance import Instance
from typing import List

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
    
