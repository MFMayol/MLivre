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
            # printeamos la que se ha agregado la orden
            print(f"Orden {orden_seleccionada.index} agregada a la solución con {sum(orden_seleccionada.items.values())} ítems.")
        else:
            print("No hay órdenes candidatas que se puedan agregar a la solución con el stock disponible.")
            return solucion_antigua
        
        # si se modifica se actualiza toda la solución

        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        # agregamos la orden seleccionada a la selected orders de la solución
        solucion.selected_orders = tuple(solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas)

        solucion.actualizar_atributos()

        # Retornamos la solución modificada
        return solucion