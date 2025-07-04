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
        self.total_units = sum(self.items.values())

    def __str__(self):
        """
        Representación en cadena de la orden.

        Returns:
            str: Cadena que representa la orden y sus ítems.
        """
        return f"Order {self.index}: {self.items} (Total units: {self.total_units})"


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
        self.total_units = sum(self.stock.values())
        
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
    
    def __str__(self):
        """
        Representación en cadena del corredor.

        Returns:
            str: Cadena que representa el corredor y su stock.
        """
        return f"Runner {self.index}: {self.stock}, Total units: {self.total_units})"


