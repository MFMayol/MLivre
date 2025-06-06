from data_structures import Order, Runner
from collections import defaultdict
from typing import Dict, List
import copy


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
        
    def asignar_ordenes(self, ordenes_seleccionadas: List[Order], corredores_seleccionados: List[Runner]):
        """
        Realiza una asignación dada una solución encontrada del problema
        
        Args:
        ordenes_seleccionadas: Lista de órdenes seleccionadas.
        corredores_seleccionados: Lista de corredores seleccionados.
        
        Returns:
        Tuple con:
            - asignacion: Dict[order][runner][item] = cantidad_asignada
            - stock_restante: Dict[runner][item] = stock restante después de la asignación
    """
        asignacion = defaultdict(lambda: defaultdict(dict))
        pasillos_seleccionados = copy.deepcopy(corredores_seleccionados)
        stock_restante = {pasillo.index: pasillo.stock.copy() for pasillo in pasillos_seleccionados}

        for order in ordenes_seleccionadas:
            for item_id, demanda_item in order.items.items():
                demanda_restante = demanda_item

                for runner in corredores_seleccionados:
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

        return asignacion, stock_restante

    def constructora(self): #Heurística Greedy de construcción de solución
        """
        Construye una solución factible a partir de una instancia del problema y luego aplica una heurística de asignación.

        Paso 1: Selecciona órdenes en orden decreciente de unidades hasta superar el LB.
        Paso 2: Selecciona corredores también en orden decreciente de capacidad,
                hasta que se puede satisfacer toda la demanda de las órdenes seleccionadas.

        Args:
            None

        Returns:
            Solucion: Solución con las órdenes y corredores seleccionados.
            asignacion: Diccionario con la asignación de órdenes a pasillos
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
            
        asignacion, stock_restante = self.asignar_ordenes(ordenes_seleccionadas, corredores_seleccionados)

        return Solucion(selected_orders=ordenes_seleccionadas, selected_runners= corredores_seleccionados, instance= self, asignacion = asignacion, stock_restante = stock_restante) #metodo constructora retorna un objeto Solucion y el diccionario de stock restante


class Solucion:
    """
    Clase que representa una solución al problema.

    Atributos:
        selected_orders (List[Order]): Lista de órdenes seleccionadas para la solución.
        selected_runners (List[Runner]): Lista de corredores seleccionados para abastecer la demanda.
        instance (Instance): Instancia del problema.
        asignacion (Dict): Diccionario de la forma Dict[order_id][runner_id][item_id] = cantidad_asignada
        stock_restante (Dict) Diccionario de la forma Dict[runner_id][item_id] = cantidad
    """
    def __init__(self, selected_orders: List[Order], selected_runners: List[Runner], instance : Instance, asignacion : Dict, stock_restante : Dict):
        self.selected_orders = selected_orders
        self.selected_runners = selected_runners
        self.instance = instance
        self.asignacion = asignacion
        self.stock_restante = stock_restante

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
        demanda_total = {i:0 for i in range(self.instance.num_items)}
        
        for order in self.selected_orders:
            for item, quantity in order.items.items():
                demanda_total[item] = demanda_total.get(item, 0) + quantity

        # ahora vemos la cantidad de productos que se llevan de cada uno en todos los pasillos en un diccionario
        stock_total = {i:0 for i in range(self.instance.num_items)}
        for runner in self.selected_runners:
            for item, quantity in runner.stock.items():
                stock_total[item] = stock_total.get(item, 0) + quantity

        # ahora vemos si la cantidad de productos solicitados en las ordenes seleccionadas es mayor o igual que la cantidad de productos que se llevan en cada pasillo
        return all(stock_total[i] >= demanda_total[i] for i in demanda_total)
    
    # Low level (evaluar si se pueden añadir órdenes con el stock restante)
    def evaluar_stock_restante(self):
        """
        Intenta agregar órdenes no seleccionadas a la solución actual si hay suficiente stock y no se excede el UB.

        Returns:
            Solucion: Nuevo objeto Solucion con órdenes adicionales si es posible.
        """
        UB = self.instance.ub
        ordenes_sobrantes = [orden for orden in self.instance.orders if orden not in set(self.selected_orders)] #deberian ser la 1,2,4
        
        nueva_asignacion = copy.deepcopy(self.asignacion)
        nuevo_stock_restante = copy.deepcopy(self.stock_restante)
        nuevas_ordenes = list(self.selected_orders) #no debería modificar lo original
        unidades_actuales = sum(o.total_units for o in self.selected_orders)
        
        for orden in ordenes_sobrantes:
            if unidades_actuales + orden.total_units > UB: #nos saltamos las ordenes que vuelven infactible la solucion
                continue 
        
            demanda_ok = True
            stock_necesario = {} #stock de la orden
            
            for item, cantidad in orden.items.items(): #revisar para cada item de la orden si hay suficiente stock sobrante
                cantidad_restante = cantidad # cantidad del item que se pide en la orden / al asignar en pasillos iremos restando (por eso es cantidad_restante)
                stock_total = sum(nuevo_stock_restante[r.index].get(item, 0) for r in self.selected_runners) # sumamos la cantidad total de stock del item que estamos iterando dentro de los pasillos de la solución
                if stock_total < cantidad_restante: # si no hay stock, rompemos el for y pasamos a una nueva orden
                    demanda_ok = False
                    break
                
                stock_necesario[item] = [] # diccionario de la forma {item(indice): [(corredor, unidades), (corredor, unidades)]}
                for runner in self.selected_runners: # queremos recorrer los pasillos activos
                    disponible = nuevo_stock_restante[runner.index].get(item, 0) #obtenemos la cantidad de stock disponible del item en cada pasillo (del ciclo)
                    if disponible > 0: # si hay stock lo asignamos
                        tomar = min(disponible, cantidad_restante) # asignamos lo maximo disponible (minimo entre disponible y demanda)
                        stock_necesario[item].append((runner.index, tomar)) # guardamos la asignacion 
                        cantidad_restante -= tomar # restamos de la demanda lo que asignamos en el pasillo
                        if cantidad_restante == 0: # cuando terminamos de asignar el item rompemos el ciclo
                            break
                        
                             
            if not demanda_ok: # si demanda_ok = False pasamos a la siguiente orden
                continue
            
            #Aplicamos la asignación:
            for item, asignaciones in stock_necesario.items(): # recordar forma: {item(indice): [(corredor, unidades), (corredor, unidades)]}
                for runner_id, cantidad in asignaciones: # actualizamos el diccionario de asignacion y de stock_restante
                    nueva_asignacion[orden.index][runner_id][item] = cantidad
                    nuevo_stock_restante[runner_id][item] -= cantidad

        nuevas_ordenes.append(orden)
        unidades_actuales += orden.total_units
        
        return Solucion(selected_orders=nuevas_ordenes, selected_runners=self.selected_runners, instance=self.instance, asignacion=nueva_asignacion, stock_restante=nuevo_stock_restante)
        
    
        
       
              
            
        
         
        
        
        
        

    # ahora creamos el print para que se vea mejor
    def __str__(self):
        return f"Solución con {len(self.selected_orders)} órdenes y {len(self.selected_runners)} corredores con un ratio de {self.objective_value():.2f}"

