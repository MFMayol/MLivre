import numpy as np
from Instance import Instance
import copy, random
from Solucion import Solucion
import time
from gurobipy import Model, GRB, quicksum
#Falta agregar que elimine 1 pasillo que tenga menos productos y agregar 1 pasillo con muchos productos
# Falta que agregue 1 orden con muchos productos


class LowLevels:
    '''Clase que representa los niveles bajos del algoritmo de optimización.'''
    def __init__(self, id: int):
        self.id = id

    def implementacion(solucion: Solucion) -> Solucion:
        ''' Metodo abstracto que debe ser implementado por las subclases. '''
        raise NotImplementedError("Este método debe ser implementado por las subclases.")

class LL_eliminacion_ordenes_random(LowLevels):
    'LL de eliminación de pasillos tomando un 5% al azar de las seleccionadas'

    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 10% de las ordenes seleccionadas'''
        solucion = solucion_antigua.clone()
        p = random.choice([0,0.05,0.1])

        num_to_remove = max(1,int(p * solucion.num_orders))

        if not solucion.selected_orders or num_to_remove >= len(solucion.selected_orders):
            return solucion 

        # Elegir aleatoriamente cuáles eliminar
        orders_to_remove = random.sample(solucion.selected_orders, num_to_remove)

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_orders = [order for order in solucion.selected_orders if order not in orders_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()
        
        return solucion

class LL_eliminacion_ordenes_chicas(LowLevels):
    'LL de eliminación de pasillos tomando un 5% las ordenes más chicas'

    def __init__(self, id ):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 10% de las ordenes seleccionadas'''
        solucion = solucion_antigua.clone()
        p = random.choice([0,0.05,0.1])
        num_to_remove = max(1,int(p * solucion.num_orders))

        if not solucion.selected_orders or num_to_remove >= len(solucion.selected_orders):
            return solucion 

        sorter_orders = sorted(solucion.selected_orders, key=lambda o: o.total_units, reverse= False)

        # Elegir aleatoriamente cuáles eliminar
        orders_to_remove = sorter_orders[num_to_remove:]

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_orders = [order for order in solucion.selected_orders if order not in orders_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()
        
        return solucion

class LL_eliminacion_ordenes_grandes(LowLevels):
    'LL de eliminación de pasillos tomando un 5% las ordenes más chicas'

    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 10% de las ordenes seleccionadas'''
        solucion = solucion_antigua.clone()
        p = random.choice([0,0.05,0.1])
        num_to_remove = max(1,int(p * solucion.num_orders))

        if not solucion.selected_orders or num_to_remove >= len(solucion.selected_orders):
            return solucion 

        sorter_orders = sorted(solucion.selected_orders, key=lambda o: o.total_units, reverse= True)

        # Elegir aleatoriamente cuáles eliminar
        orders_to_remove = sorter_orders[num_to_remove:]

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_orders = [order for order in solucion.selected_orders if order not in orders_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()
        
        return solucion

class LL_eliminacion_pasillos_malos(LowLevels):
    'LL eliminacion de pasillos tomando un 5% que tiene menos productos asociados'
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 5% de los pasillos seleccionados'''
        solucion = solucion_antigua.clone()
        num_to_remove = max(1,int(0.05 * solucion.num_runners))

        if not solucion.selected_runners or num_to_remove > solucion.num_runners:
            return solucion
        # Ordenar corredores por total_units ascendente
        sorted_runners = sorted(solucion.selected_runners, key=lambda r: r.total_units)

        # Seleccionar corredores a eliminar
        runners_to_remove = sorted_runners[num_to_remove:]

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_runners = [runner for runner in solucion.selected_runners if runner not in runners_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()

        return solucion
    
class LL_eliminacion_pasillo_malo(LowLevels):
    'LL eliminacion de pasillos tomando un 5% que tiene menos productos asociados'
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 5% de los pasillos seleccionados'''
        solucion = copy.deepcopy(solucion_antigua)
        num_to_remove = min(1,solucion.num_runners)

        if not solucion.selected_runners or num_to_remove > solucion.num_runners:
            return solucion
        # Ordenar corredores por total_units ascendente
        sorted_runners = sorted(solucion.selected_runners, key=lambda r: r.total_units)

        # Seleccionar corredores a eliminar
        runners_to_remove = sorted_runners[num_to_remove:]

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_runners = [runner for runner in solucion.selected_runners if runner not in runners_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()

        return solucion
    
class LL_eliminacion_pasillos_malos_diversity(LowLevels):
    'LL eliminacion de pasillos tomando un 5% que tiene menos tipos de ítems'
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 5% de los pasillos seleccionados'''
        solucion = solucion_antigua.clone()
        num_to_remove = max(1,int(0.05 * solucion.num_runners))

        if not solucion.selected_runners or num_to_remove > solucion.num_runners:
            return solucion
        # Ordenar corredores por total_units ascendente
        sorted_runners = sorted(solucion.selected_runners, key=lambda r: len(r.stock))

        # Seleccionar corredores a eliminar
        runners_to_remove = sorted_runners[num_to_remove:]

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_runners = [runner for runner in solucion.selected_runners if runner not in runners_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()

        return solucion

class LL_eliminacion_pasillos_random(LowLevels):
    'LL eliminacion de pasillos random tomando un 10% al azar'
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 5% de los pasillos seleccionados'''
        solucion = solucion_antigua.clone()
        p = random.choice([0.05,0.1])

        num_to_remove = max(1,int(p * solucion.num_orders))

        if not solucion.selected_runners or num_to_remove > solucion.num_runners:
            return solucion

        # Elegir aleatoriamente cuáles eliminar
        runners_to_remove = random.sample(solucion.selected_runners, num_to_remove)

        # Filtrar la lista para quitar esas órdenes
        solucion.selected_runners = [runner for runner in solucion.selected_runners if runner not in runners_to_remove]

        # Actualizar atributos dependientes
        solucion.actualizar_atributos()

        return solucion

class LL_agregacion_ordenes_random(LowLevels):
    '''Agrega el 5% de las ordenes no seleccionadas de forma random'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n órdenes a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()
        
        # Identificar órdenes no seleccionadas
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]
        
        p = random.choice([0.05,0.1])
        # Calcular n como 10% del upper bound y pasarlo a entero
        n = max(1,int(p * len(ordenes_no_seleccionadas)))


        # Limitar n al tamaño máximo disponible
        n = min(n, len(ordenes_no_seleccionadas))

        # Si no hay órdenes para agregar, retornar la solución original
        if n == 0:
            return solucion_antigua
        
        # Seleccionar n órdenes al azar
        ordenes_agregar = random.sample(ordenes_no_seleccionadas, n)
        
        # Agregar los ids de las nuevas órdenes
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
        
        # Actualizar id_selected_orders como set
        solucion.id_selected_orders = set(id_ordenes_seleccionadas)
        
        # Actualizar selected_orders como lista
        solucion.selected_orders = [solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas]

        # Actualizar los atributos derivados
        solucion.actualizar_atributos()

        # Retornar la nueva solución
        return solucion

class LL_agregacion_ordenes_chicas(LowLevels):
    '''Implementación de la primera low level de agregación'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n órdenes a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()
        
        # Identificar órdenes no seleccionadas
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]
        p = random.choice([0.05,0.1])
        # Calcular n como 10% del upper bound y pasarlo a entero
        n = max(1,int(p * len(ordenes_no_seleccionadas)))

        # Si no hay órdenes para agregar, retornar la solución original
        if n == 0:
            return solucion_antigua
        
        sorter_orders = sorted(ordenes_no_seleccionadas, key=lambda r: r.total_units, reverse= False)
        # Seleccionar n órdenes al azar
        ordenes_agregar = sorter_orders[n:]
        
        # Agregar los ids de las nuevas órdenes
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
        
        # Actualizar id_selected_orders como set
        solucion.id_selected_orders = set(id_ordenes_seleccionadas)
        
        # Actualizar selected_orders como lista
        solucion.selected_orders = [solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas]

        # Actualizar los atributos derivados
        solucion.actualizar_atributos()

        # Retornar la nueva solución
        return solucion
    
class LL_agregacion_orden_chica(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega la orden más chica a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = copy.deepcopy(solucion_antigua)
        
        # Identificar órdenes no seleccionadas
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]

        # Calcular n como 10% del upper bound y pasarlo a entero
        n = min(1,len(ordenes_no_seleccionadas))

        # Si no hay órdenes para agregar, retornar la solución original
        if n == 0:
            return solucion_antigua
        
        sorter_orders = sorted(ordenes_no_seleccionadas, key=lambda r: r.total_units, reverse= True)
        # Seleccionar n órdenes al azar
        ordenes_agregar = sorter_orders[n:]
        
        # Agregar los ids de las nuevas órdenes
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
        
        # Actualizar id_selected_orders como set
        solucion.id_selected_orders = set(id_ordenes_seleccionadas)
        
        # Actualizar selected_orders como lista
        solucion.selected_orders = [solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas]

        # Actualizar los atributos derivados
        solucion.actualizar_atributos()

        # Retornar la nueva solución
        return solucion

class LL_agregacion_ordenes_chicas_diversity(LowLevels):
    '''Implementación de la primera low level de agregación segun diversidad'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n órdenes a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()
        
        # Identificar órdenes no seleccionadas
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]
        p = random.choice([0.05,0.1])
        # Calcular n como 10% del upper bound y pasarlo a entero
        n = max(1,int(p * len(ordenes_no_seleccionadas)))

        # Si no hay órdenes para agregar, retornar la solución original
        if n == 0:
            return solucion_antigua
        
        sorter_orders = sorted(ordenes_no_seleccionadas, key=lambda r: len(r.items), reverse= False)
        # Seleccionar n órdenes al azar
        ordenes_agregar = sorter_orders[n:]
        
        # Agregar los ids de las nuevas órdenes
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
        
        # Actualizar id_selected_orders como set
        solucion.id_selected_orders = set(id_ordenes_seleccionadas)
        
        # Actualizar selected_orders como lista
        solucion.selected_orders = [solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas]

        # Actualizar los atributos derivados
        solucion.actualizar_atributos()

        # Retornar la nueva solución
        return solucion

class LL_agregacion_ordenes_grandes_diversity(LowLevels):
    '''Implementación de la primera low level de agregación segun diversidad'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n órdenes a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()
        
        # Identificar órdenes no seleccionadas
        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]
        p = random.choice([0.05,0.1])
        # Calcular n como 10% del upper bound y pasarlo a entero
        n = max(1,int(p * len(ordenes_no_seleccionadas)))

        # Si no hay órdenes para agregar, retornar la solución original
        if n == 0:
            return solucion_antigua
        
        sorter_orders = sorted(ordenes_no_seleccionadas, key=lambda r: len(r.items), reverse= True)
        # Seleccionar n órdenes al azar
        ordenes_agregar = sorter_orders[n:]
        
        # Agregar los ids de las nuevas órdenes
        for orden in ordenes_agregar:
            id_ordenes_seleccionadas.append(orden.index)
        
        # Actualizar id_selected_orders como set
        solucion.id_selected_orders = set(id_ordenes_seleccionadas)
        
        # Actualizar selected_orders como lista
        solucion.selected_orders = [solucion.instance.orders[id_orden] for id_orden in id_ordenes_seleccionadas]

        # Actualizar los atributos derivados
        solucion.actualizar_atributos()

        # Retornar la nueva solución
        return solucion
    
class LL_agregacion_ordenes_faciles(LowLevels):
    '''
    Agrega órdenes cuya demanda ya está mayormente cubierta por el stock actual.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()

        stock_actual = solucion.stock_seleccionado

        ordenes_disponibles = [
            orden for orden in solucion.instance.orders
            if orden.index not in solucion.id_selected_orders
        ]

        # Define qué tan "cubierta" está la orden
        def cobertura(orden):
            cubierta = sum(
                min(stock_actual.get(i, 0), q)
                for i, q in orden.items.items()
            )
            return cubierta / (orden.total_units + 1e-5)

        # Ordenar por cobertura descendente
        ordenes_disponibles.sort(key=cobertura, reverse=True)

        k = max(1, int(0.05 * len(ordenes_disponibles)))
        ordenes_agregar = ordenes_disponibles[:k]

        solucion.selected_orders.extend(ordenes_agregar)
        solucion.id_selected_orders.update(o.index for o in ordenes_agregar)
        solucion.actualizar_atributos()
        return solucion

class LL_agregacion_pasillos_top(LowLevels):
    '''Implementación de la segunda low level de agregación'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n pasillos con la mayor cantidad de items a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()
        
        # Identificar pasillos no seleccionados
        id_runners_seleccionados = list(solucion.id_selected_runners)
        runners_no_seleccionados = [
            solucion.instance.runners[id_runner]
            for id_runner in solucion.instance.id_runners
            if id_runner not in id_runners_seleccionados
        ]
        p = random.choice([0.05,0.1])
        n = int(p * len(runners_no_seleccionados))

        # Si no hay pasillos disponibles para agregar, retornar solución original
        if n == 0:
            return solucion_antigua
        
        # vemos los pasillos con más items
        sorted_runners = sorted(runners_no_seleccionados, key=lambda r: r.total_units, reverse= True)
        
        # Seleccionar n pasillos al azar
        runners_agregar = sorted_runners[n:]
        
        # Agregar ids de los nuevos pasillos
        for runner in runners_agregar:
            id_runners_seleccionados.append(runner.index)
        
        # Actualizar id_selected_runners como set
        solucion.id_selected_runners = set(id_runners_seleccionados)

        # Actualizar selected_runners como lista
        solucion.selected_runners = [solucion.instance.runners[id_runner] for id_runner in id_runners_seleccionados]

        # Actualizar atributos derivados
        solucion.actualizar_atributos()

        # Retornar nueva solución
        return solucion

class LL_agregacion_pasillos_random(LowLevels):
    '''Implementación de la segunda low level de agregación'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n pasillos a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()

        # Identificar pasillos no seleccionados
        id_runners_seleccionados = list(solucion.id_selected_runners)
        runners_no_seleccionados = [
            solucion.instance.runners[id_runner]
            for id_runner in solucion.instance.id_runners
            if id_runner not in id_runners_seleccionados
        ]

        p = random.choice([0.05,0.1])

        # Calcular n como 5% de los pasillos totales
        n = int(p* len(runners_no_seleccionados))
        # Limitar n al tamaño disponible
        n = min(n, len(runners_no_seleccionados))

        # Si no hay pasillos disponibles para agregar, retornar solución original
        if n == 0:
            return solucion_antigua
        
        # Seleccionar n pasillos al azar
        runners_agregar = random.sample(runners_no_seleccionados, n)
        
        # Agregar ids de los nuevos pasillos
        for runner in runners_agregar:
            id_runners_seleccionados.append(runner.index)
        
        # Actualizar id_selected_runners como set
        solucion.id_selected_runners = set(id_runners_seleccionados)

        # Actualizar selected_runners como lista
        solucion.selected_runners = [solucion.instance.runners[id_runner] for id_runner in id_runners_seleccionados]

        # Actualizar atributos derivados
        solucion.actualizar_atributos()

        # Retornar nueva solución
        return solucion
    
class LL_agregacion_pasillos_random_ub(LowLevels):
    '''Implementación de la segunda low level de agregación'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n pasillos a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = solucion_antigua.clone()

        # Identificar pasillos no seleccionados
        id_runners_seleccionados = list(solucion.id_selected_runners)
        runners_no_seleccionados = [
            solucion.instance.runners[id_runner]
            for id_runner in solucion.instance.id_runners
            if id_runner not in id_runners_seleccionados
        ]

        p = (solucion.instance.lb+1)/(solucion.instance.ub)

        # Calcular n como 5% de los pasillos totales
        n = int(p* len(runners_no_seleccionados))
        # Limitar n al tamaño disponible
        n = min(n, len(runners_no_seleccionados))

        # Si no hay pasillos disponibles para agregar, retornar solución original
        if n == 0:
            return solucion_antigua
        
        # Seleccionar n pasillos al azar
        runners_agregar = random.sample(runners_no_seleccionados, n)
        
        # Agregar ids de los nuevos pasillos
        for runner in runners_agregar:
            id_runners_seleccionados.append(runner.index)
        
        # Actualizar id_selected_runners como set
        solucion.id_selected_runners = set(id_runners_seleccionados)

        # Actualizar selected_runners como lista
        solucion.selected_runners = [solucion.instance.runners[id_runner] for id_runner in id_runners_seleccionados]

        # Actualizar atributos derivados
        solucion.actualizar_atributos()

        # Retornar nueva solución
        return solucion

class LL_agregacion_pasillo_orden_top(LowLevels):
    '''Ll que agrega el pasillo con más elementos y la orden con más elementos'''
    def __init__(self, id):
        super().__init__(id)
    def implementacion(self, solucion_antigua):
        solucion = solucion_antigua.clone()

        id_runners_seleccionados = list(solucion.id_selected_runners)
        runners_no_seleccionados = [
            solucion.instance.runners[id_runner]
            for id_runner in solucion.instance.id_runners
            if id_runner not in id_runners_seleccionados
        ]

        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_no_seleccionadas = [
            solucion.instance.orders[id_orden]
            for id_orden in solucion.instance.id_orders
            if id_orden not in id_ordenes_seleccionadas
        ]

        #vemos los pasillos con más items
        sorted_runners = sorted(runners_no_seleccionados, key=lambda r: r.total_units, reverse= True)
        
        # Seleccionar n pasillos al azar
        runners_agregar = sorted_runners[0:]
        
        # Agregar ids de los nuevos pasillos
        for runner in runners_agregar:
            id_runners_seleccionados.append(runner.index)



        #vemos las ordenes con más items
        sorted_orders = sorted(ordenes_no_seleccionadas, key=lambda r: r.total_units, reverse= True)
        
        # Seleccionar n pasillos al azar
        ordenes_agregar = sorted_orders[0:]
        
        # Agregar ids de los nuevos pasillos
        for order in ordenes_agregar:
            id_ordenes_seleccionadas.append(order.index)
        # Actualizar atributos derivados
        solucion.actualizar_atributos()

        # Retornar nueva solución
        return solucion
    
class LL_agregacion_pasillos_eficientes(LowLevels):
    '''
    Agrega pasillos que tienen mayor eficiencia en cubrir demanda pendiente.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()
        
        if solucion.is_factible:
            return solucion  # Ya es factible, no hace falta cambiar
        
        # Demanda pendiente = demanda - stock actual
        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado
        demanda_pendiente = {
            i: max(demanda[i] - stock.get(i, 0), 0)
            for i in demanda
        }

        # Pasillos no seleccionados
        corredores_disponibles = [
            runner for runner in solucion.instance.runners
            if runner.index not in solucion.id_selected_runners
        ]

        # Eficiencia: cuánto stock útil aporta respecto a lo que se necesita
        def eficiencia(runner):
            utilidad = sum(
                min(runner.stock.get(i, 0), demanda_pendiente[i])
                for i in demanda_pendiente
            )
            return utilidad / (sum(runner.stock.values()) + 1e-5)  # Evitar división por cero

        corredores_disponibles.sort(key=eficiencia, reverse=True)

        # Agregar top k pasillos más eficientes
        k = max(1, int(0.05 * len(corredores_disponibles)))
        corredores_agregar = corredores_disponibles[:k]

        solucion.selected_runners.extend(corredores_agregar)
        solucion.id_selected_runners.update(r.index for r in corredores_agregar)
        solucion.actualizar_atributos()
        return solucion

class LL_factibilizar_demanda(LowLevels):
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua):
        tiempo_inicio = time.time()

        solucion = solucion_antigua.clone()

        if solucion.is_factible == True:
            return solucion

        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado

        for id_prod in list(demanda.keys()):
            while demanda[id_prod] > stock.get(id_prod, 0):
                if time.time() - tiempo_inicio > 2:
                    break

                ordenes_con_producto = [order for order in solucion.selected_orders if order.items.get(id_prod, 0) > 0]

                if not ordenes_con_producto:
                    break

                ordenes_con_producto.sort(key=lambda o: o.items.get(id_prod, 0), reverse=True)
                orden_a_eliminar = ordenes_con_producto[0]
                solucion.selected_orders.remove(orden_a_eliminar)
                solucion.id_selected_orders.discard(orden_a_eliminar.index)

                solucion.actualizar_atributos()
                demanda = solucion.demanda_ordenes_selecccionadas
                stock = solucion.stock_seleccionado
        return solucion

class LL_factibilizar_UB(LowLevels):
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua):
        tiempo_inicio = time.time()

        solucion = solucion_antigua.clone()
        if solucion.is_factible == True:
            return solucion

        while solucion.total_units_orders > solucion.instance.ub:
            if time.time() - tiempo_inicio > 2:
                break

            if not solucion.selected_orders:
                break

            solucion.selected_orders.sort(key=lambda o: o.total_units, reverse=True)
            orden_a_eliminar = solucion.selected_orders[0]
            solucion.selected_orders.remove(orden_a_eliminar)
            solucion.id_selected_orders.discard(orden_a_eliminar.index)
            solucion.actualizar_atributos()
        return solucion
    
class LL_factibilizar_LB(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua):
        tiempo_inicio = time.time()

        solucion = solucion_antigua.clone()
        if solucion.is_factible == True:
            return solucion

        while solucion.total_units_orders < solucion.instance.lb:
            if time.time() - tiempo_inicio > 2:
                break

            ordenes_disponibles = [
                solucion.instance.orders[id_orden]
                for id_orden in solucion.instance.id_orders
                if id_orden not in solucion.id_selected_orders
            ]
            
            if not ordenes_disponibles:
                break

            ordenes_disponibles.sort(key=lambda o: o.total_units, reverse=True)
            orden_a_agregar = ordenes_disponibles[0]
            solucion.selected_orders.append(orden_a_agregar)
            solucion.id_selected_orders.add(orden_a_agregar.index)
            solucion.actualizar_atributos()

            demanda = solucion.demanda_ordenes_selecccionadas
            stock = solucion.stock_seleccionado

            exceso = any(demanda[id_prod] > stock.get(id_prod, 0) for id_prod in demanda)
            if exceso:
                solucion.selected_orders.remove(orden_a_agregar)
                solucion.id_selected_orders.discard(orden_a_agregar.index)
                solucion.actualizar_atributos()
                break

        solucion.actualizar_atributos()
        return solucion


class LL_swap_orden_danina_por_util(LowLevels):
    '''
    Elimina la orden que más contribuye al exceso de demanda
    y la reemplaza por una fácil de cubrir.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()
        stock = solucion.stock_seleccionado
        demanda = solucion.demanda_ordenes_selecccionadas

        # Calcular exceso por ítem
        exceso = {
            i: max(demanda[i] - stock.get(i, 0), 0)
            for i in demanda
        }

        # Evaluar daño por orden
        def dano(orden):
            return sum(
                min(q, exceso.get(i, 0))
                for i, q in orden.items.items()
            )

        ordenes_dentro = solucion.selected_orders
        if not ordenes_dentro:
            return solucion

        ordenes_dentro.sort(key=dano, reverse=True)
        orden_a_remover = ordenes_dentro[0]

        solucion.selected_orders.remove(orden_a_remover)
        solucion.id_selected_orders.discard(orden_a_remover.index)
        solucion.actualizar_atributos()

        # Ahora agregar orden fácil
        stock = solucion.stock_seleccionado  # actualizado
        ordenes_fuera = [
            o for o in solucion.instance.orders
            if o.index not in solucion.id_selected_orders
        ]

        def cobertura(orden):
            return sum(
                min(stock.get(i, 0), q)
                for i, q in orden.items.items()
            ) / (orden.total_units + 1e-5)

        ordenes_fuera.sort(key=cobertura, reverse=True)
        for orden in ordenes_fuera:
            solucion.selected_orders.append(orden)
            solucion.id_selected_orders.add(orden.index)
            solucion.actualizar_atributos()
            break  # Solo una

        return solucion


class LL_dinkelbach_un_iter(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua = Solucion):
        solucion_copia = solucion_antigua.clone()
        instance = solucion_copia.instance
        orders = instance.orders
        runners = instance.runners
        lb = instance.lb
        ub = instance.ub
        I = set(i for order in orders for i in order.items.keys())
        O = {o.index for o in orders}
        A = {a.index for a in runners}
        order_dict = {o.index: o for o in orders}
        runner_dict = {a.index: a for a in runners}

        q = solucion_copia.objective_value

        modelo_base = Model("Dinkelbach_LowLevel")
        modelo_base.setParam('OutputFlag', 0)
        modelo_base.setParam('TimeLimit', 5)
        modelo_base.setParam('Presolve', 0)
        modelo_base.setParam('Threads', 1)

        x = modelo_base.addVars(O, vtype=GRB.BINARY, name="x")
        y = modelo_base.addVars(A, vtype=GRB.BINARY, name="y")

        # Preprocesamiento de términos no nulos
        restricciones_i = {i: [] for i in I}
        for o in O:
            for i, val in order_dict[o].items.items():
                restricciones_i[i].append((o, val))

        rhs_i = {i: [] for i in I}
        for a in A:
            for i, val in runner_dict[a].stock.items():
                rhs_i[i].append((a, val))

        for i in I:
            lhs = quicksum(val * x[o] for o, val in restricciones_i[i])
            rhs = quicksum(val * y[a] for a, val in rhs_i[i])
            modelo_base.addConstr(lhs <= rhs, name=f"stock_{i}")

        modelo_base.addConstr(
            quicksum(order_dict[o].total_units * x[o] for o in O) <= ub,
            name="upper_bound"
        )
        modelo_base.addConstr(
            quicksum(order_dict[o].total_units * x[o] for o in O) >= lb,
            name="lower_bound"
        )

        modelo_base.setObjective(
            quicksum(order_dict[o].total_units * x[o] for o in O) - q * quicksum(y[a] for a in A),
            GRB.MAXIMIZE
        )

        modelo_base.optimize()

        x_vals = {o: x[o].X for o in O}
        y_vals = {a: y[a].X for a in A}

        ordenes_seleccionadas = [order_dict[o] for o in x_vals if x_vals[o] > 0.5]
        corredores_seleccionados = [runner_dict[a] for a in y_vals if y_vals[a] > 0.5]

        solucion = Solucion(
            selected_orders=ordenes_seleccionadas,
            selected_runners=corredores_seleccionados,
            instance=instance
        )

        return solucion