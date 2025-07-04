import numpy as np
from Instance import Instance, Solucion
import copy
import random


class LowLevels:
    '''Clase que representa los niveles bajos del algoritmo de optimización.'''
    def __init__(self, id: int, nombre: str):
        self.id = id
        self.nombre = nombre

    def implementacion(solucion: Solucion) -> Solucion:
        ''' Metodo abstracto que debe ser implementado por las subclases. '''
        raise NotImplementedError("Este método debe ser implementado por las subclases.")

##############  AGREGACIÓN DE ÓRDENES Y PASILLOS ######################################################################################################################

class LowLevel1_agregacion(LowLevels):
    '''Implementación de la primera low level de agregación'''
    def _init_(self, id: int, nombre: str):
        super()._init_(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n ordenes a la solución actual.
        '''
        # Copia de la solución actual
        solucion = copy.deepcopy(solucion_antigua)
        
        # Seleccionamos el 10% del UB como parámetro para agregar órdenes
        n = 0.1*solucion.instance.ub
        
        # Lista para actualizar la solucion
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        
        # Lista para almacenar las ordenes que no forman parte de la solución (objetos)
        ordenes_no_seleccionadas = []
        
        # Iteramos sobre las órdenes de la instancia
        for id_orden in solucion.instance.id_orders:
            # Si la orden no está en la solución, la agregamos a la lista de órdenes no seleccionadas
            if id_orden not in id_ordenes_seleccionadas:
                ordenes_no_seleccionadas.append(solucion.instance.orders[id_orden])
        
        # Si no hay órdenes no seleccionadas, retornamos la solución antigua
        if not ordenes_no_seleccionadas:
            return solucion_antigua
        
        # Seleccionamos n órdenes al azar para agregar a la solución actual
        ordenes_agregar = random.sample(ordenes_no_seleccionadas, n)
        
        # Agregamos los id de las ordenes seleccionadas a la lista:
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
            
        # Actualizamos la solución si es modificada:
        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        
        # Agregamos la orden seleccionada a selected orders de la solución
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)

        # Actualizamos la solución
        solucion.actualizar_atributos()

        # Retornamos la solución modificada
        return solucion
    
class LowLevel2_agregacion(LowLevels):
    '''Implementación de la segunda low level de agregación'''
    def _init_(self, id: int, nombre: str):
        super()._init_(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n pasillos a la solución actual.
        '''
        # Copia de la solución actual
        solucion = copy.deepcopy(solucion_antigua)
        
        # Seleccionamos el 5% del total del pasillos en la instancia
        pasillos = solucion.instance.runners
        n = 0.05 * len(pasillos)
        
        # Lista para actualizar la solucion
        id_runners_seleccionados = list(solucion.id_selected_runners)
        
        # Lista para los pasillos que no forman parte de la solución (objetos)
        runners_no_seleccionados = []
        
        # Iteramos sobre los pasillos de la instancia
        for id_runner in solucion.instance.id_runners:
            # Si es que el pasillo no es parte de la solución, se agrega a la lista de no_seleccionados
            if id_runner not in id_runners_seleccionados:
                runners_no_seleccionados.append(solucion.instance.runners[id_runner])
                
        # Si la lista es vacía retornamos la solución antigua
        if not runners_no_seleccionados:
            return solucion_antigua
        
        # Seleccionamos n pasillos a agregar
        runners_agregar = random.sample(runners_no_seleccionados, n)
        
         # Agregamos los id de los pasillos seleccionados a la lista:
        for runner in runners_agregar:
            id_runners_seleccionados.append(runner.index)
            
        # Actualizamos la solución si es modificada:
        solucion.id_selected_runners = tuple(id_runners_seleccionados)
        
        # Agregamos el pasillo seleccionado a selected runners de la solución
        solucion.selected_runners = tuple(solucion.instance.runners[id_runner] for id_runner in id_runners_seleccionados)

        # Actualizamos la solución
        solucion.actualizar_atributos()

        # Retornamos la solución modificada
        return solucion

##############  ELIMINACIÓN DE ÓRDENES Y PASILLOS ######################################################################################################################

class LowLevel1_eliminacion(LowLevels):
    '''Implementación del segundo nivel bajo del algoritmo de optimización que elimina el pasillo con menos productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Eliminamos el pasillo seleccionado con menos productos de la solución.'''
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Aquí se implementa la lógica específica del segundo nivel bajo
        pasillos_seleccionados = list(solucion_antigua.id_selected_runners)
        
        #Si no hay pasillos que seleccionar se retorna la solución antigua
        if not pasillos_seleccionados:
            return solucion_antigua
        
        # ahora ordenamos los pasillos seleccionados por el número de productos que tienen de mayor a menor
        pasillos_seleccionados.sort(key=lambda p: solucion_antigua.instance.runners[p].total_units, reverse=True)

        # elejimos el pasillo con menos productos
        pasillo_seleccionado = pasillos_seleccionados[len(pasillos_seleccionados) - 1]  # el último es el que tiene menos productos

        # eliminamos el pasillo seleccionado de la solución
        pasillos_seleccionados.remove(pasillo_seleccionado)

        solucion.id_selected_runners = tuple(pasillos_seleccionados)
        solucion.selected_runners = tuple(solucion.instance.runners[id_pasillo] for id_pasillo in pasillos_seleccionados)

        solucion.actualizar_atributos()

        return solucion

class LowLevel2_eliminacion(LowLevels):
    ''' Implementación del tercer nivel bajo del algoritmo de optimización que elimina un pasillo random de los ya seleccionados. '''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
    
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Eliminamos un pasillo seleccionado al azar de la solución.'''
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Aquí se implementa la lógica específica del tercer nivel bajo
        pasillos_seleccionados = list(solucion.id_selected_runners)
        
        #Si no hay pasillos que seleccionar se retorna la solución antigua
        if not pasillos_seleccionados:
            return solucion_antigua        
        
        # eliminamos un pasillo al azar
        id_pasillo_eliminado = np.random.choice(pasillos_seleccionados)
        #print(id_pasillo_eliminado)
        pasillos_seleccionados.remove(id_pasillo_eliminado)

        solucion.id_selected_runners = tuple(pasillos_seleccionados)
        solucion.selected_runners = tuple(solucion.instance.runners[id_pasillo] for id_pasillo in pasillos_seleccionados)

        solucion.actualizar_atributos()

        return solucion
    

##############  SWAP DE ÓRDENES Y PASILLOS ######################################################################################################################


class LowLevel1_swap(LowLevels):
    ''' Implementación del cuarto nivel bajo que elimina la orden con menos productos y agrega una orden con más productos no seleccionada. '''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Eliminamos la orden con menos productos y agregamos una orden con más productos no seleccionada.'''
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Aquí se implementa la lógica específica del cuarto nivel bajo
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)

        # ahora buscamos una orden no seleccionada que se pueda agregar a la solución al azar
        # creamos una lista de órdenes no seleccionadas
        ordenes_no_seleccionadas = []
        for id_orden in solucion.instance.id_orders:
            if id_orden not in id_ordenes_seleccionadas:
                ordenes_no_seleccionadas.append(solucion.instance.orders[id_orden])

        # elejimos la orden con menos productos
        ordenes_seleccionadas = list(solucion.selected_orders)
        
        #si no se selecciona ninguna orden, retorna la solución antigua
        if not ordenes_seleccionadas:
            return solucion_antigua
        
        ordenes_seleccionadas.sort(key=lambda o: o.total_units)
        orden_seleccionada = ordenes_seleccionadas[0]
        # eliminamos la orden seleccionada de la solución
        id_ordenes_seleccionadas.remove(orden_seleccionada.index)

        # elejimos una orden no seleccionada al azar
        if ordenes_no_seleccionadas:
            orden_seleccionada = np.random.choice(ordenes_no_seleccionadas)

        # agregamos la orden seleccionada a la solución
        id_ordenes_seleccionadas.append(orden_seleccionada.index)
        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)

        # actualizamos los atributos de la solución
        solucion.actualizar_atributos()

        # retornamos la solución modificada
        return solucion
    

############## FACTIBILIZADORAS ######################################################################################################################

class LowLevel1_factibilizadora(LowLevels):
    '''Revisa si existe infactibilidad en UB y la factibiliza eliminando órdenes hasta entrar en el UB'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        if solucion.total_units_order > solucion.instance.ub:
            # Ordena las órdenes seleccionadas de menor a mayor en unidades
            ordenes_ordenadas = sorted(solucion.selected_orders, key=lambda o: o.total_units)

            unidades_actuales = solucion.total_units_order
            nuevas_ordenes = list(solucion.selected_orders)
            nuevas_ids = list(solucion.id_selected_orders)

            for orden in ordenes_ordenadas:
                if unidades_actuales <= solucion.instance.ub:
                    break
                unidades_actuales -= orden.total_units
                nuevas_ordenes.remove(orden)
                nuevas_ids.remove(orden.index)

            solucion.selected_orders = tuple(nuevas_ordenes)
            solucion.id_selected_orders = tuple(nuevas_ids)
            solucion.actualizar_atributos()

            return solucion
        
        else:
            return solucion_antigua
    
class LowLevel2_factibilizadora(LowLevels):
    '''Revisa si existe infactibilidad en LB y la factibiliza agregando órdenes hasta cumplir el LB.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        if solucion.total_units_order < solucion.instance.lb:
            unidades_actuales = solucion.total_units_order
            nuevas_ordenes = list(solucion.selected_orders)
            nuevas_ids = list(solucion.id_selected_orders)

            # Obtener las órdenes fuera de la solución
            ordenes_fuera = [
                orden for orden in solucion.instance.orders
                if orden.index not in solucion.id_selected_orders
            ]

            # Ordenar por unidades de menor a mayor para agregar "barato"
            ordenes_ordenadas = sorted(ordenes_fuera, key=lambda o: o.total_units)

            for orden in ordenes_ordenadas:
                if unidades_actuales >= solucion.instance.lb:
                    break
                if unidades_actuales + orden.total_units > solucion.instance.ub:
                    continue  # Evita pasarse del límite superior

                nuevas_ordenes.append(orden)
                nuevas_ids.append(orden.index)
                unidades_actuales += orden.total_units

            solucion.selected_orders = tuple(nuevas_ordenes)
            solucion.id_selected_orders = tuple(nuevas_ids)
            solucion.actualizar_atributos()

            return solucion
        else:
            return solucion_antigua
        
        
class LowLevel3_factibilizadora(LowLevels):
    '''Revisa si existe infactibilidad en las consistencias y agrega más pasillos con ese ítem'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        if len(solucion.infesible_type()[2]) == 0:
            return solucion  # No hay infactibilidad por stock insuficiente

        for i in solucion.demanda_total_por_item:
            if solucion.demanda_total_por_item[i] > solucion.stock_total_por_item[i]:
                item = i
                break
        else:
            return solucion  # No encontró ítems con demanda insatisfecha

        nuevos_runners = list(solucion.selected_runners)
        nuevas_ids = list(solucion.id_selected_runners)

        runners_fuera_item = [
            runner for runner in solucion.instance.runners
            if runner.index not in solucion.id_selected_runners
            and item in runner.stock
        ]
        print(item)

        runners_ordenados = sorted(runners_fuera_item, key=lambda r: r.total_units, reverse=True)

        for runner in runners_ordenados:
            if solucion.stock_total_por_item[item] >= solucion.demanda_total_por_item[item]:
                break
            nuevos_runners.append(runner)
            nuevas_ids.append(runner.index)

            # actualizar stock manualmente
            solucion.stock_total_por_item[item] += runner.stock.get(item, 0)

        solucion.selected_runners = tuple(nuevos_runners)
        solucion.id_selected_runners = tuple(nuevas_ids)
        solucion.actualizar_atributos()

        return solucion
