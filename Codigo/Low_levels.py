import numpy as np
from Instance import Instance, Solucion
import copy

class LowLevels:
    '''Clase que representa los niveles bajos del algoritmo de optimización.'''
    def __init__(self, id: int, nombre: str):
        self.id = id
        self.nombre = nombre

    def implementacion(solucion: Solucion) -> Solucion:
        ''' Metodo abstracto que debe ser implementado por las subclases. '''
        raise NotImplementedError("Este método debe ser implementado por las subclases.")
    

class LowLevel1(LowLevels):
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
        
        # ahora, si hay órdenes candidatas, seleccionamos la que tiene máscantidad de todos los ítems
        if ordenes_candidatas:
            # Seleccionamos la orden con más ítems
            orden_seleccionada = max(ordenes_candidatas, key=lambda o: sum(o.items.values()))
            # Agregamos la orden seleccionada a la solución siempre y cuando no se superen los limites de productos posibles de llevar Upper Bound
            if solucion.total_units + orden_seleccionada.total_units > solucion.instance.ub:
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
    

class LowLevel2(LowLevels):
    '''Implementacion de lov level que agrega a la solución la orden con menos productos.'''
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
    

class LowLevel3(LowLevels):
    '''Implementación del segundo nivel bajo del algoritmo de optimización que elimina el pasillo con menos productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Eliminamos el pasillo seleccionado con menos productos de la solución.'''
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Aquí se implementa la lógica específica del segundo nivel bajo
        pasillos_seleccionados = list(solucion_antigua.id_selected_runners)
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

class LowLevel4(LowLevels):
    ''' Implementación del tercer nivel bajo del algoritmo de optimización que elimina un pasillo random de los ya seleccionados. '''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
    
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''Eliminamos un pasillo seleccionado al azar de la solución.'''
        # creamos una copia de la solución para no modificar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Aquí se implementa la lógica específica del tercer nivel bajo
        pasillos_seleccionados = list(solucion.id_selected_runners)
        
        # eliminamos un pasillo al azar
        id_pasillo_eliminado = np.random.choice(pasillos_seleccionados)
        pasillos_seleccionados.remove(id_pasillo_eliminado)

        solucion.id_selected_runners = tuple(pasillos_seleccionados)
        solucion.selected_runners = tuple(solucion.instance.runners[id_pasillo] for id_pasillo in pasillos_seleccionados)

        solucion.actualizar_atributos()

        return solucion

class LowLevel5(LowLevels):
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
        ordenes_seleccionadas.sort(key=lambda o: o.total_units)
        orden_seleccionada = ordenes_seleccionadas[0]
        # eliminamos la orden seleccionada de la solución
        id_ordenes_seleccionadas.remove(orden_seleccionada.index)


        # elejimos una orden no seleccionada al azar
        orden_seleccionada = np.random.choice(ordenes_no_seleccionadas)
        # agregamos la orden seleccionada a la solución
        id_ordenes_seleccionadas.append(orden_seleccionada.index)
        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)

        # actualizamos los atributos de la solución
        solucion.actualizar_atributos()

        # retornamos la solución modificada
        return solucion

