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
    '''Implementación del primer nivel bajo del algoritmo de optimización que agrega la orden con más productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Implementación del primer nivel bajo del algoritmo de optimización el cual consiste en determinar todas las ordenes que se pueden agregar
        a la solución utilizando el stock restante, luego se elije la que tiene más items y se agrega a la selección.'''
        # Aquí se implementa la lógica específica del primer nivel bajo
        # Obtenemos el stock disponible por ítem
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        id_ordenes_seleccionadas = list(solucion.id_selected_orders)

        stock_disponible = solucion.stock_disponible_por_item
        # Creamos una lista para almacenar las ordenes que no están en la solución actual
        ordenes_no_seleccionadas = []
        # Iteramos sobre las órdenes de la solución
        for id_orden in solucion.instance.id_orders:
            # Si la orden no está en la solución, la agregamos a la lista de órdenes no seleccionadas
            if id_orden not in id_ordenes_seleccionadas:
                ordenes_no_seleccionadas.append(solucion.instance.orders[id_orden])

        # Si no hay órdenes no seleccionadas, retornamos la solución antigua
        if not ordenes_no_seleccionadas:
            #print("No hay órdenes no seleccionadas para agregar a la solución.")
            return solucion_antigua
        
        # ahora determinamos si de las ordenes no seleccionadas, hay alguna que se pueda agregar a la solución con el stock disponible
        ordenes_candidatas = []
        for orden in ordenes_no_seleccionadas:
            # Verificamos si la orden se puede agregar con el stock disponible
            if all(stock_disponible[item] >= cantidad for item, cantidad in orden.items.items()):
                ordenes_candidatas.append(orden)
        
        # ahora, si hay órdenes candidatas, seleccionamos la que tiene más cantidad de todos los ítems
        if ordenes_candidatas:
            # Seleccionamos la orden con más ítems
            orden_seleccionada = max(ordenes_candidatas, key=lambda o: sum(o.items.values()))
            # Agregamos la orden seleccionada a la solución siempre y cuando no se superen los limites de productos posibles de llevar Upper Bound
            if solucion.total_units_order + orden_seleccionada.total_units > solucion.instance.ub:
                return solucion_antigua
            
            id_ordenes_seleccionadas.append(orden_seleccionada.index)
        else:
            #print("No hay órdenes candidatas que se puedan agregar a la solución con el stock disponible.")
            return solucion_antigua
        
        # si se modifica se actualiza toda la solución

        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        # agregamos la orden seleccionada a la selected orders de la solución
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)

        solucion.actualizar_atributos()

        # Retornamos la solución modificada
        return solucion
    

class LowLevel2_agregacion(LowLevels):
    '''Implementacion de low level que agrega a la solución la orden con menos productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
    
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Implementación del segundo nivel bajo del algoritmo de optimización que consiste en agregar la orden con menos productos a la solución, independientemente de la factibilidad.'''
        # Aquí se implementa la lógica específica del segundo nivel bajo
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        # Obtenemos las órdenes no seleccionadas
        ordenes_no_seleccionadas = []
        for id_orden in solucion.instance.id_orders:
            if id_orden not in id_ordenes_seleccionadas:
                ordenes_no_seleccionadas.append(solucion.instance.orders[id_orden])
        
        # elegimos la orden con menos productos
        if not ordenes_no_seleccionadas:
            #print("No hay órdenes no seleccionadas para agregar a la solución.")
            return solucion_antigua
        
        ordenes_no_seleccionadas.sort(key=lambda o: o.total_units)
        orden_seleccionada = ordenes_no_seleccionadas[0]
        # Agregamos la orden seleccionada a la solución
        id_ordenes_seleccionadas.append(orden_seleccionada.index)
        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        # agregamos la orden seleccionada a la selected orders de la solución
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)
        # actualizamos los atributos de la solución
        solucion.actualizar_atributos()
        # Retornamos la solución modificada
        return solucion
    
class LowLevel3_agregacion(LowLevels):
    '''Agrega órdenes con base en el ítem más diverso (sobrante) en stock.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)

        # Obtener órdenes fuera de la solución
        ordenes_fuera = [
            orden for orden in solucion.instance.orders
            if orden.index not in id_ordenes_seleccionadas
        ]

        if not ordenes_fuera:
            return solucion_antigua

        n = len(ordenes_fuera)
        cantidad_agregar = random.randint(1, min(10, n))

        # Mapeo de pesos por índice 
        r_i = {orden.index: len(orden.items) / n for orden in ordenes_fuera}

        # Selección aleatoria ponderada
        ordenes_idx_seleccionadas = random.choices(
            population=list(r_i.keys()),
            weights=list(r_i.values()),
            k=cantidad_agregar
        )

        for idx in ordenes_idx_seleccionadas:
            if idx not in id_ordenes_seleccionadas:
                id_ordenes_seleccionadas.append(idx)

        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        solucion.selected_orders = tuple(
            solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas
        )
        solucion.actualizar_atributos()
        return solucion
    
class LowLevel4_agregacion(LowLevels):
    '''Agrega una cantidad n de pasillos disponibles con más productos'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
        
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        id_runners_seleccionados = list(solucion.id_selected_runners)
        
        # Obtenemos los runners no seleccionadas
        runners_no_seleccionados = []
        for id_runner in solucion.instance.id_runners:
            if id_runner not in id_runners_seleccionados:
                runners_no_seleccionados.append(solucion.instance.runners[id_runner])
        
        n=min(10, len(runners_no_seleccionados))
        n = len(runners_no_seleccionados)
        cantidad_agregar = random.randint(1, min(10, n))
        runners_no_seleccionados.sort(key=lambda r: r.total_units, reverse=True)   
        runners_seleccionados = runners_no_seleccionados[0:cantidad_agregar]
        # Agregamos la orden seleccionada a la solución
        for runner in runners_seleccionados:
            id_runners_seleccionados.append(runner.index)
            
        solucion.id_selected_runners = tuple(id_runners_seleccionados)
        # agregamos la orden seleccionada a la selected orders de la solución
        solucion.selected_runners = tuple(solucion.instance.runners[id_runner] for id_runner in id_runners_seleccionados)
        # actualizamos los atributos de la solución
        solucion.actualizar_atributos()
        # Retornamos la solución modificada
        return solucion
    
class LowLevel5_agregacion(LowLevels):
    '''Implementacion de low level que agrega a la solución las n órdenes con más productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
    
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Implementación del segundo nivel bajo del algoritmo de optimización que consiste en agregar la orden con menos productos a la solución, independientemente de la factibilidad.'''
        # Aquí se implementa la lógica específica del segundo nivel bajo
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        # Obtenemos las órdenes no seleccionadas
        ordenes_no_seleccionadas = []
        for id_orden in solucion.instance.id_orders:
            if id_orden not in id_ordenes_seleccionadas:
                ordenes_no_seleccionadas.append(solucion.instance.orders[id_orden])
        
        # elegimos la orden con menos productos
        if not ordenes_no_seleccionadas:
            #print("No hay órdenes no seleccionadas para agregar a la solución.")
            return solucion_antigua
        
        n = len(ordenes_no_seleccionadas)
        cantidad_agregar = random.randint(1, min(10, n))
        ordenes_no_seleccionadas.sort(key=lambda o: o.total_units, reverse=True)
        orden_seleccionada = ordenes_no_seleccionadas[0:cantidad_agregar]
        # Agregamos la orden seleccionada a la solución
        id_ordenes_seleccionadas.append(orden_seleccionada.index)
        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        # agregamos la orden seleccionada a la selected orders de la solución
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)
        # actualizamos los atributos de la solución
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
    
class LowLevel2_swap(LowLevels):
    '''Agrega un pasillo con probabilidad proporcional a su cantidad de ítems y elimina otro con probabilidad inversa.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        A_s = list(solucion.id_selected_runners)
        A_sC = [a for a in solucion.instance.id_runners if a not in A_s]

        if not A_sC or len(A_s) <= 1:
            return solucion_antigua

        total_fuera = sum(sum(solucion.instance.runners[a].stock.values()) for a in A_sC)
        if total_fuera == 0:
            return solucion_antigua

        probabilidades_agregar = [sum(solucion.instance.runners[a].stock.values()) / total_fuera for a in A_sC]
        a_agregado = np.random.choice(A_sC, p=probabilidades_agregar)
        A_s_nuevo = A_s + [a_agregado]

        A_s_filtrado = [a for a in A_s if a != a_agregado]
        if not A_s_filtrado:
            return solucion_antigua

        total_dentro = sum(sum(solucion.instance.runners[a].stock.values()) for a in A_s_filtrado)
        if total_dentro == 0:
            return solucion_antigua

        probabilidades_eliminar = [1 - sum(solucion.instance.runners[a].stock.values()) / total_dentro for a in A_s_filtrado]
        suma_probs = sum(probabilidades_eliminar)
        probabilidades_eliminar = [p / suma_probs for p in probabilidades_eliminar]
        a_eliminado = np.random.choice(A_s_filtrado, p=probabilidades_eliminar)

        A_final = [a for a in A_s_nuevo if a != a_eliminado]
        solucion.id_selected_runners = tuple(A_final)
        solucion.selected_runners = tuple(solucion.instance.runners[a] for a in A_final)
        solucion.actualizar_atributos()
        return solucion


class LowLevel3_swap(LowLevels):
    '''Agrega una orden con probabilidad proporcional a su tamaño y elimina otra con probabilidad inversa.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        O_s = list(solucion.id_selected_orders)
        O_sC = [o for o in solucion.instance.id_orders if o not in O_s]

        if not O_sC or len(O_s) <= 1:
            return solucion_antigua

        total_fuera = sum(solucion.instance.orders[o].total_units for o in O_sC)
        if total_fuera == 0:
            return solucion_antigua

        probabilidades_agregar = [solucion.instance.orders[o].total_units / total_fuera for o in O_sC]
        o_agregado = np.random.choice(O_sC, p=probabilidades_agregar)
        O_s_nuevo = O_s + [o_agregado]

        O_s_filtrado = [o for o in O_s if o != o_agregado]
        if not O_s_filtrado:
            return solucion_antigua

        total_dentro = sum(solucion.instance.orders[o].total_units for o in O_s_filtrado)
        if total_dentro == 0:
            return solucion_antigua

        probabilidades_eliminar = [1 - solucion.instance.orders[o].total_units / total_dentro for o in O_s_filtrado]
        suma_probs = sum(probabilidades_eliminar)
        probabilidades_eliminar = [p / suma_probs for p in probabilidades_eliminar]
        o_eliminado = np.random.choice(O_s_filtrado, p=probabilidades_eliminar)

        O_final = [o for o in O_s_nuevo if o != o_eliminado]
        solucion.id_selected_orders = tuple(O_final)
        solucion.selected_orders = tuple(solucion.instance.orders[o] for o in O_final)
        solucion.actualizar_atributos()
        return solucion
    

############## FACTIBILIZADORAS ######################################################################################################################

class LowLevel1_factibilizadora(LowLevels):
    '''Revisa si existe infactibilidad en UB y la factibiliza eliminando órdenes hasta entrar en el UB de menor a mayor cantidad de productos'''
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
    '''Revisa si existe infactibilidad en LB y la factibiliza agregando órdenes hasta cumplir el LB de menor a mayor cantidad de productos.'''
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
            return solucion
        
        for i in solucion.demanda_total_por_item:
            if solucion.demanda_total_por_item[i] > solucion.stock_total_por_item[i]:
                item = i
                break
        nuevos_runners = list(solucion.selected_runners)
        nuevas_ids = list(solucion.id_selected_runners)
        
        faltante_item_i = solucion.demanda_total_por_item[item] - solucion.stock_total_por_item[item]
        
        #recoge todos los runners fuera con el ítem i
        runners_fuera_item = [runner for runner in solucion.instance.runners
                         if runner.index not in solucion.id_selected_runners
                         and item in runner.stock.keys()]
        

        # Ordenar por unidades de mayor a menor para agregar runners
        runners_ordenados = sorted(runners_fuera_item, key=lambda r: r.total_units, reverse=True)

        for runner in runners_ordenados:
            if solucion.stock_total_por_item[item] >= solucion.demanda_total_por_item[item]:
                break

            nuevos_runners.append(runner)
            nuevas_ids.append(runner.index)
            unidades_actuales += runner.total_units

        solucion.selected_runners = tuple(nuevos_runners)
        solucion.id_selected_orders = tuple(nuevas_ids)
        solucion.actualizar_atributos()

        return solucion