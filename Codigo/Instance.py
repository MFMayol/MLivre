from data_structures import Order, Runner  # Importación de clases de estructuras de datos externas
from typing import Dict, List  # Importación de tipos para anotaciones
import copy  # Importación para realizar copias profundas de objetos complejos


class Instance:
    """
    Representa una instancia del problema de optimización con órdenes y corredores disponibles.

    Atributos:
        orders (List[Order]): Lista de órdenes disponibles.
        runners (List[Runner]): Lista de corredores disponibles.
        num_items (int): Número total de tipos de ítems distintos.
        lb (int): Límite inferior de unidades para formar una wave.
        ub (int): Límite superior de unidades para formar una wave.
    """
    def __init__(self, orders: List[Order], runners: List[Runner], num_items: int, lb: int, ub: int):
        self.orders = orders
        self.runners = runners
        self.num_items = num_items
        self.lb = lb
        self.ub = ub
        # Convertimos los generadores a tuplas inmediatamente
        self.id_orders = set(order.index for order in orders)  # Ahora es una tupla
        self.id_runners = set(runner.index for runner in runners) # Ahora es una tupla






    def __str__(self):
        """
        Retorna una representación legible de la instancia actual.

        Returns:
            str: Descripción textual de la instancia.
        """
        return f"Instance with {len(self.orders)} orders and {len(self.runners)} runners, covering {self.num_items} item"
