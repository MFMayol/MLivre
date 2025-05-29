from typing import Dict, List

class Order:
    """
    Representa una orden compuesta por varios ítems y sus cantidades solicitadas.

    Attributes:
        index (int): Índice de la orden (de 0 a o - 1).
        items (Dict[int, int]): Diccionario con item_id como clave y cantidad solicitada como valor.
    """

    def __init__(self, index: int, items: Dict[int, int]):
        self.index = index
        self.items = items

    def total_units(self) -> int:
        """
        Calcula el total de unidades solicitadas en la orden.

        Returns:
            int: Número total de unidades de todos los ítems en la orden.
        """
        return sum(self.items.values())


class Runner:
    """
    Representa un corredor con un stock limitado de ítems disponibles.

    Attributes:
        index (int): Índice del corredor (de 0 a a - 1).
        stock (Dict[int, int]): Diccionario con item_id como clave y unidades disponibles como valor.
    """

    def __init__(self, index: int, stock: Dict[int, int]):
        self.index = index
        self.stock = stock

    def can_fulfill(self, item_id: int, quantity: int) -> bool:
        """
        Verifica si el corredor puede abastecer una cantidad específica de un ítem.

        Args:
            item_id (int): ID del ítem.
            quantity (int): Cantidad solicitada.

        Returns:
            bool: True si el corredor puede cumplir con la cantidad solicitada, False en caso contrario.
        """
        return self.stock.get(item_id, 0) >= quantity


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