from data_structures import Order, Runner
from collections import defaultdict
from typing import Dict, List
import copy
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

    def constructora(self): #Heurística Greedy de construcción de solución
        """
        Construye una solución factible a partir de una instancia del problema.

        Paso 1: Selecciona órdenes en orden decreciente de unidades hasta superar el LB.
        Paso 2: Selecciona corredores también en orden decreciente de capacidad,
                hasta que se puede satisfacer toda la demanda de las órdenes seleccionadas.

        Args:
            None

        Returns:
            Solucion: Solución con las órdenes y corredores seleccionados.
        """
        LB = self.lb

        # Ordenar las órdenes por mayor cantidad total de unidades
        ordenes_ordenadas = sorted(self.orders, key=lambda o: o.total_units, reverse=True) #self.orders es una lista de las ordenes (objetos)
        ordenes_seleccionadas = []
        total_unidades = 0

        # Seleccionar órdenes hasta superar el Upper Bound
        for orden in ordenes_ordenadas: # recorremos la lista de ordenes_ordenadas y las seleccionamos hasta que se cumpla LB 
            ordenes_seleccionadas.append(orden) # agregamos una orden a la lista
            total_unidades += orden.total_units # actualizamos la cantidad de items a llevar
            if total_unidades > LB: # revisar si superamos le límite LB
                    break

        # Calcular demanda total de productos por ítem
        demanda_total = {i:0 for i in range(self.num_items)} # rellenamos un diccionario de la forma item:0 / usamos self.num_items directamente pq es un atributo de la clase Instance (y constructora es un metodo dentro de la clase, luego el self que se le pasa es de Instance)
        for orden in ordenes_seleccionadas: # recorremos la lista de ordenes seleccionadas
            for item, qty in orden.items.items(): # para cada orden, generamos una tupla (item, cantidad) a partir del diccionario del objeto
                demanda_total[item] += qty # sumamos todas las cantidades y las agregamos al diccionario de demanda total

        # Ordenar corredores por mayor capacidad total
        corredores_ordenados = sorted(self.runners, key=lambda r: sum(r.stock.values()), reverse=True) #self.runners es una lista de pasillos (objetos)
        corredores_seleccionados = []
        stock_disponible = defaultdict(int)

        for corredor in corredores_ordenados:
            for item, qty in corredor.stock.items(): # misma logica de la tupla de antes
                stock_disponible[item] += qty # rellenamos el diccionario con item:stock
            corredores_seleccionados.append(corredor) #agregamos el corredor a la lista

            # Verificar si el stock ya cubre toda la demanda
            cubre_demanda = all(stock_disponible[i] >= demanda_total[i] for i in demanda_total)
            if cubre_demanda:
                break

        return Solucion(selected_orders=ordenes_seleccionadas, selected_runners= corredores_seleccionados, instance= self) #metodo constructora retorna un objeto Solucion


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
    
    #Heurística de asignación de órdenes:
    def asignar_ordenes(self) -> Dict[int, Dict[int, Dict[int, int]]]: # cuanto de cada item de cada orden va en cada pasillo
        """
        Asigna los ítems de las órdenes seleccionadas a múltiples corredores si es necesario.

        Returns:
            Dict[order_id][runner_id][item_id] = cantidad_asignada
        """
        asignacion = defaultdict(lambda: defaultdict(dict))
        
        pasillos_seleccionados = copy.deepcopy(self.selected_runners)
        stock_restante = {pasillo.index: pasillo.stock for pasillo in pasillos_seleccionados} #diccionario que copia el stock para ir revisando cada pasillo
        
        for order in self.selected_orders: # recorremos cada orden de la solucion
            for item_id, demanda_item in order.items.items(): # recorremos la tupla de (item, demanda) de cada orden
                demanda_restante = demanda_item

                # Recorremos corredores hasta cumplir la demanda del ítem
                for runner in self.selected_runners:
                    runner_stock = stock_restante[runner.index].get(item_id, 0)
                    if runner_stock <= 0:
                        continue

                    cantidad_asignada = min(runner_stock, demanda_restante)
                    if cantidad_asignada > 0:
                        asignacion[order.index][runner.index][item_id] = cantidad_asignada
                        stock_restante[runner.index][item_id] -= cantidad_asignada
                        demanda_restante -= cantidad_asignada

                    if demanda_restante == 0:
                        break

                if demanda_restante > 0:
                    raise ValueError(f"No hay stock suficiente para el ítem {item_id} de la orden {order.index}")

        return asignacion

    # ahora creamos el print para que se vea mejor
    def __str__(self):
        return f"Solución con {len(self.selected_orders)} órdenes y {len(self.selected_runners)} corredores con un ratio de {self.objective_value():.2f}"

