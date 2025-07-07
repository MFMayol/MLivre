
from data_structures import Order, Runner  # Importación de clases de estructuras de datos externas
from typing import Dict, List  # Importación de tipos para anotaciones
import copy  #
from Instance import Instance

class Solucion:
    """
    Clase que representa una solución factible al problema de asignación de órdenes a corredores.

    Atributos:
        selected_orders (List[Order]): Órdenes seleccionadas.
        selected_runners (List[Runner]): Corredores seleccionados.
        instance (Instance): Instancia del problema a la que pertenece la solución.
    """
    def __init__(self, selected_orders: List[Order], selected_runners: List[Runner], instance: Instance):
        self.selected_orders = selected_orders
        self.selected_runners = selected_runners
        self.instance = instance
        self.total_units_orders = sum(order.total_units for order in selected_orders)  # Total de unidades entregadas
        self.num_runners = len(selected_runners)  # Número de corredores usados
        self.num_orders = len(selected_orders) # numero de ordenes seleccionadas
        self.is_factible = self.set_is_factible()  # Factibilidad de la solución (True o False)
        self.objective_value = self.set_objective_value()  # Valor objetivo de la solución (Float)
        self.demanda_ordenes_selecccionadas = self.determinar_demanda_ordenes_selecccionadas() # Diccionario con la demanda de cada producto { id_producto: demanda}
        self.stock_seleccionado = self.determinar_stock_seleccionado() # Dict con los productos en los pasillos seleccionados {id_producto: stock}
        #self.holgura = self.determinar_holgura() #Diccionario que tiene la diferencia entre stock - demanda por item
        self.id_selected_orders = set(order.index for order in selected_orders)  # Tupla de índices de órdenes seleccionadas
        self.id_selected_runners = set(runner.index for runner in selected_runners)  # Tupla de índices de corredores seleccionados

    def actualizar_atributos(self):
        """
        Actualiza los atributos de la solución después de realizar cambios en las órdenes o corredores seleccionados.
        """
        self.total_units_orders = sum(order.total_units for order in self.selected_orders)  # Total de unidades entregadas
        self.num_runners = len(self.selected_runners)  # Número de corredores usados
        self.num_orders = len(self.selected_orders) # numero de ordenes seleccionadas
        self.is_factible = self.set_is_factible()  # Factibilidad de la solución (True o False)
        self.objective_value = self.set_objective_value()  # Valor objetivo de la solución (Float)
        self.demanda_ordenes_selecccionadas = self.determinar_demanda_ordenes_selecccionadas() # Diccionario con la demanda de cada producto { id_producto: demanda}
        self.stock_seleccionado = self.determinar_stock_seleccionado() # Dict con los productos en los pasillos seleccionados {id_producto: stock}
        self.id_selected_orders = set(order.index for order in self.selected_orders)
        self.id_selected_runners = set(runner.index for runner in self.selected_runners)
        self.is_factible = self.set_is_factible()
        #self.holgura = self.determinar_holgura()

    def actualizar_ordenes_seleccionadar(self):
        self.selected_orders
    def set_objective_value(self) -> float:
        """
        Calcula el valor objetivo como la razón entre total de unidades y número de corredores.
        
        Returns:
            float: Valor objetivo de la solución.
        """
        valor_objetivo = 0

        if self.is_factible == False:
            valor_objetivo -= 10000

        if self.num_runners == 0:
            return 0.0
        return self.total_units_orders / self.num_runners


    def set_is_factible(self) -> bool:
        """
        Verifica si la solución cumple con que el stock total cubre la demanda total.

        Returns:
            bool: True si la solución es factible, False en caso contrario.
        """
        demanda_total = {i: 0 for i in range(self.instance.num_items)}  # Inicializa demanda total por ítem
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total[item] += quantity

        stock_total = {i: 0 for i in range(self.instance.num_items)}  # Inicializa stock total por ítem
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_total[item] += quantity

        
        # verificamos si la solucion respespeta el lb y el ub respecto a los items totales
        if self.total_units_orders < self.instance.lb or self.total_units_orders > self.instance.ub:
            return False

        # Verifica si el stock cubre la demanda en todos los ítems
        return all(stock_total[i] >= demanda_total[i] for i in demanda_total)

    def determinar_stock_seleccionado(self):
        stock_total_por_item = {i: 0 for i in range(self.instance.num_items)}  # Inicializa stock total por ítem
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_total_por_item[item] += quantity
        return stock_total_por_item
    
    def determinar_demanda_ordenes_selecccionadas(self):
        demanda_total_por_item = {i: 0 for i in range(self.instance.num_items)}  # Inicializa demanda total por ítem
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total_por_item[item] += quantity
        return demanda_total_por_item
    
    def determinar_holgura(self):
        holgura = {}
        for id in range(self.instance.num_items):
            holgura[id] = max(0, self.stock_seleccionado.get(id, 0) - self.demanda_ordenes_selecccionadas.get(id, 0))
        return holgura

    def __str__(self):
        """
        Retorna una representación legible de la solución actual.

        Returns:
            str: Descripción textual de la solución.
        """
        return f"La solución escoje {self.num_orders} ordenes y {self.num_runners} pasillos. Las ordenes {self.id_selected_orders} con un total de {self.total_units_orders} unidades y los corredores {self.id_selected_runners} con un valor objetivo de {self.objective_value:.2f}."

    def costo_infactible(self) -> float:
        """
        Devuelve la suma de los restantes que hacen a las restricciones infactibles
        """
        demanda_total = {i: 0 for i in range(self.instance.num_items)}  # Inicializa demanda total por ítem
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total[item] += quantity

        stock_total = {i: 0 for i in range(self.instance.num_items)}  # Inicializa stock total por ítem
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_total[item] += quantity

        
        # verificamos si la solucion respespeta el lb y el ub respecto a los items totales
        if self.total_units_orders < self.instance.lb:
            k_1 = self.instance.lb - self.total_units_orders
        else:
            k_1 = 0
        
        if self.total_units_orders > self.instance.ub:
            k_2 = self.total_units_orders - self.instance.ub
        else:
            k_2 = 0
        
        k = []  
        for i in demanda_total:
            if stock_total[i] < demanda_total[i]:
                k_i = demanda_total[i] - stock_total[i]
                k.append(k_i)

        return k_1+k_2+sum(k)
    
    def clone(self) -> "Solucion":
        """
        Crea una copia de la solución actual sin usar deepcopy, copiando solo las listas de órdenes y pasillos seleccionados.
        """
        new_orders = list(self.selected_orders)
        new_runners = list(self.selected_runners)

        return Solucion(
            selected_orders=new_orders,
            selected_runners=new_runners,
            instance=self.instance  # compartida, ya que es inmutable
    )
