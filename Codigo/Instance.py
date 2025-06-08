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
        self.id_orders = tuple(order.index for order in orders)  # Ahora es una tupla
        self.id_runners = tuple(runner.index for runner in runners) # Ahora es una tupla

    def constructora1(self):
        """
        Heurística Greedy que construye una solución factible.
        Paso 1: Selecciona órdenes en orden decreciente de unidades hasta superar el LB.
        Paso 2: Selecciona corredores con mayor capacidad hasta cubrir la demanda total.

        Returns:
            Solucion: Objeto con las órdenes y corredores seleccionados.
        """
        LB = self.lb

        # Ordena las órdenes en orden decreciente según la cantidad total de unidades
        ordenes_ordenadas = sorted(self.orders, key=lambda o: o.total_units, reverse=False)

        ordenes_seleccionadas = []  # Lista para almacenar las órdenes seleccionadas
        total_unidades = 0  # Acumulador de unidades seleccionadas

        # Itera sobre las órdenes hasta alcanzar o superar el LB
        for orden in ordenes_ordenadas:
            ordenes_seleccionadas.append(orden)
            total_unidades += orden.total_units
            if total_unidades > LB:
                break  # Sale del ciclo al superar el límite inferior

        # Inicializa diccionario con demanda total por ítem (todos los ítems en 0)
        demanda_total = {i: 0 for i in range(self.num_items)}

        # Suma la demanda total por ítem de las órdenes seleccionadas
        for orden in ordenes_seleccionadas:
            for item, qty in orden.items.items():
                demanda_total[item] += qty

        # Ordena corredores por capacidad total disponible (suma de stock)
        corredores_ordenados = sorted(self.runners, key=lambda r: sum(r.stock.values()), reverse=True)

        corredores_seleccionados = []  # Lista de corredores que serán seleccionados
        stock_disponible = {i: 0 for i in range(self.num_items)}  # Inicialización del stock total disponible

        # Itera sobre corredores hasta cubrir toda la demanda
        for corredor in corredores_ordenados:
            corredores_seleccionados.append(corredor)  # Agrega el corredor a la selección
            # Suma el stock del corredor al stock disponible total
            for item, qty in corredor.stock.items():
                stock_disponible[item] += qty  # Acumula el stock del corredor
            
            # Verifica si el stock actual cubre toda la demanda
            if all(stock_disponible[i] >= demanda_total[i] for i in demanda_total):
                break
            else:
                continue  # Si no cubre la demanda, continúa con el siguiente corredor



        # Retorna una instancia de la solución construida
        return Solucion(
            selected_orders=ordenes_seleccionadas,
            selected_runners=corredores_seleccionados,
            instance=self
        )
    

    def constructora2(self):
        """
        Heurística Greedy que construye una solución factible.
        Paso 1: Selecciona órdenes en orden decreciente de unidades hasta superar el LB.
        Paso 2: Selecciona corredores con mayor capacidad hasta cubrir la demanda total.

        Returns:
            Solucion: Objeto con las órdenes y corredores seleccionados.
        """
        LB = self.lb
        UB = self.ub
        promedio = (LB + UB) / 2  # Calcula el promedio entre LB y UB

        # Ordena las órdenes en orden decreciente según la cantidad total de unidades
        ordenes_ordenadas = sorted(self.orders, key=lambda o: o.total_units, reverse=False)

        ordenes_seleccionadas = []  # Lista para almacenar las órdenes seleccionadas
        total_unidades = 0  # Acumulador de unidades seleccionadas

        # Itera sobre las órdenes hasta alcanzar o superar el LB
        for orden in ordenes_ordenadas:
            ordenes_seleccionadas.append(orden)
            total_unidades += orden.total_units
            if total_unidades > promedio:
                break  # Sale del ciclo al superar el límite inferior

        # Inicializa diccionario con demanda total por ítem (todos los ítems en 0)
        demanda_total = {i: 0 for i in range(self.num_items)}

        # Suma la demanda total por ítem de las órdenes seleccionadas
        for orden in ordenes_seleccionadas:
            for item, qty in orden.items.items():
                demanda_total[item] += qty

        # Ordena corredores por capacidad total disponible (suma de stock)
        corredores_ordenados = sorted(self.runners, key=lambda r: sum(r.stock.values()), reverse=True)

        corredores_seleccionados = []  # Lista de corredores que serán seleccionados
        stock_disponible = {i: 0 for i in range(self.num_items)}  # Inicialización del stock total disponible

        # Itera sobre corredores hasta cubrir toda la demanda
        for corredor in corredores_ordenados:
            corredores_seleccionados.append(corredor)  # Agrega el corredor a la selección
            # Suma el stock del corredor al stock disponible total
            for item, qty in corredor.stock.items():
                stock_disponible[item] += qty  # Acumula el stock del corredor
            
            # Verifica si el stock actual cubre toda la demanda
            if all(stock_disponible[i] >= demanda_total[i] for i in demanda_total):
                break
            else:
                continue  # Si no cubre la demanda, continúa con el siguiente corredor



        # Retorna una instancia de la solución construida
        return Solucion(
            selected_orders=ordenes_seleccionadas,
            selected_runners=corredores_seleccionados,
            instance=self
        )






    def __str__(self):
        """
        Retorna una representación legible de la instancia actual.

        Returns:
            str: Descripción textual de la instancia.
        """
        return f"Instance with {len(self.orders)} orders and {len(self.runners)} runners, covering {self.num_items} item"


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
        self.total_units = sum(order.total_units for order in selected_orders)  # Total de unidades entregadas
        self.num_runners = len(selected_runners)  # Número de corredores usados
        self.objective_value = self.set_objective_value()  # Valor objetivo de la solución
        self.is_factible = self.set_is_factible()  # Factibilidad de la solución
        self.stock_disponible_por_item = self.determinar_stock_disponible_por_item()  # Stock disponible por ítem
        self.id_selected_orders = tuple(order.index for order in selected_orders)  # Tupla de índices de órdenes seleccionadas
        self.id_selected_runners = tuple(runner.index for runner in selected_runners)  # Tupla de índices de corredores seleccionados
        


    def set_objective_value(self) -> float:
        """
        Calcula el valor objetivo como la razón entre total de unidades y número de corredores.
        
        Returns:
            float: Valor objetivo de la solución.
        """
        if self.num_runners == 0:
            return 0.0
        return self.total_units / self.num_runners

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
        if self.total_units < self.instance.lb or self.total_units > self.instance.ub:
            return False

        # Verifica si el stock cubre la demanda en todos los ítems
        return all(stock_total[i] >= demanda_total[i] for i in demanda_total)

    def asignar_ordenes(self) -> Dict[int, Dict[int, Dict[int, int]]]:
        """
        Asigna los ítems de las órdenes seleccionadas a corredores disponibles.

        Returns:
            Dict: Estructura anidada con la cantidad asignada por ítem, por orden y corredor.
        """
        asignacion = {}  # Diccionario de asignación final

        # Crea una copia profunda de los corredores para manipular el stock sin alterar el original
        pasillos_seleccionados = copy.deepcopy(self.selected_runners)

        # Diccionario para llevar un control del stock restante por corredor
        stock_restante = {pasillo.index: dict(pasillo.stock) for pasillo in pasillos_seleccionados}

        for order in self.selected_orders:
            order_id = order.index
            asignacion[order_id] = {}  # Inicializa asignación por orden

            for item_id, demanda_item in order.items.items():
                demanda_restante = demanda_item

                for runner in self.selected_runners:
                    runner_id = runner.index
                    if runner_id not in asignacion[order_id]:
                        asignacion[order_id][runner_id] = {}

                    # Obtiene el stock disponible del corredor para el ítem actual
                    runner_stock = stock_restante[runner_id].get(item_id, 0)

                    if runner_stock <= 0:
                        continue  # Salta si no hay stock disponible

                    # Calcula la cantidad a asignar al corredor
                    cantidad_asignada = min(runner_stock, demanda_restante)

                    if cantidad_asignada > 0:
                        asignacion[order_id][runner_id][item_id] = cantidad_asignada
                        stock_restante[runner_id][item_id] -= cantidad_asignada
                        demanda_restante -= cantidad_asignada

                    if demanda_restante == 0:
                        break  # Sale si la demanda del ítem fue completamente asignada

                if demanda_restante > 0:
                    # Lanza excepción si no se puede satisfacer completamente la demanda del ítem
                    raise ValueError(f"No hay stock suficiente para el ítem {item_id} de la orden {order_id}")

        return asignacion  # Retorna la asignación completa

    def determinar_stock_disponible_por_item(self) -> Dict[int, int]:
        """
        Determina el stock total disponible por ítem en los corredores seleccionados.

        Returns:
            Dict[int, int]: Diccionario con el stock total por ítem.
        """
        stock_disponible = {i: 0 for i in range(self.instance.num_items)}
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_disponible[item] += quantity
        
        # ahora restamos el stock disponible con la demanda total de las órdenes seleccionadas
        demanda_total = {i: 0 for i in range(self.instance.num_items)}
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total[item] += quantity
        
        for item in stock_disponible:
            stock_disponible[item] -= demanda_total[item]
        return stock_disponible
    
    def actualizar_atributos(self):
        """
        Actualiza los atributos de la solución después de realizar cambios en las órdenes o corredores seleccionados.
        """
        self.total_units = sum(order.total_units for order in self.selected_orders)
        self.num_runners = len(self.selected_runners)
        self.objective_value = self.set_objective_value()
        self.stock_disponible_por_item = self.determinar_stock_disponible_por_item()
        self.id_selected_orders = tuple(order.index for order in self.selected_orders)
        self.id_selected_runners = tuple(runner.index for runner in self.selected_runners)
        self.is_factible = self.set_is_factible()

    def __str__(self):
        """
        Retorna una representación legible de la solución actual.

        Returns:
            str: Descripción textual de la solución.
        """
        return f"La solución escoje las ordenes {self.id_selected_orders} con un total de {self.total_units} unidades y los corredores {self.id_selected_runners} con un valor objetivo de {self.objective_value:.2f}."
