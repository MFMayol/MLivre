import numpy as np
from Instance import Instance
import copy, random
from Solucion import Solucion
import time, heapq
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
    
class LL_eliminar_runners_ineficientes_por_densidad(LowLevels):
    """
    Elimina hasta dos corredores seleccionados cuya eficiencia para cubrir demanda es baja 
    en relación a la cantidad de ítems que ofrecen.

    Eficiente y segura incluso en instancias grandes. Útil para limpiar pasillos redundantes 
    y mejorar la eficiencia unidades/pasillo.
    """
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()

        # Verificación inicial: no hay corredores
        if solucion.num_runners == 0:
            return solucion

        demanda = solucion.demanda_ordenes_selecccionadas

        # Función de eficiencia: utilidad sobre cantidad de ítems distintos
        def utilidad_por_densidad(runner):
            utilidad = sum(min(demanda.get(i, 0), q) for i, q in runner.stock.items())
            densidad = utilidad / (len(runner.stock) + 1e-5)  # evitar división por cero
            return densidad

        # Ordenamos corredores por menor eficiencia
        corredores_ordenados = sorted(solucion.selected_runners, key=utilidad_por_densidad)

        # Eliminamos hasta 2 de los menos eficientes, si hay suficientes
        to_remove = corredores_ordenados[:min(2, len(corredores_ordenados))]

        for corredor in to_remove:
            solucion.selected_runners.remove(corredor)
            solucion.id_selected_runners.discard(corredor.index)

        solucion.actualizar_atributos()
        return solucion

class LL_eliminar_monoitems_dificiles(LowLevels):
    '''
    Elimina órdenes que solo contienen un ítem y cuya demanda es difícil de cubrir con el stock actual.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        stock = solucion.stock_seleccionado

        # Identificar órdenes monoproducto (solo tienen un ítem)
        ordenes_mono = [
            orden for orden in solucion.selected_orders
            if len(orden.items) == 1
        ]

        # Filtrar las que causan problemas de stock (no cubiertas)
        ordenes_daninas = []
        for orden in ordenes_mono:
            item, cantidad = list(orden.items.items())[0]  # único ítem
            if stock.get(item, 0) < cantidad:
                ordenes_daninas.append((orden, cantidad - stock.get(item, 0)))

        # Ordenar por mayor dificultad (más déficit)
        ordenes_daninas.sort(key=lambda x: x[1], reverse=True)

        if not ordenes_daninas:
            return solucion

        # Eliminar una o dos órdenes más conflictivas
        to_remove = [od[0] for od in ordenes_daninas[:2]]
        for orden in to_remove:
            solucion.selected_orders.remove(orden)
            solucion.id_selected_orders.discard(orden.index)

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
 
class LL_agregar_ordenes_concentradas_en_items_comunes(LowLevels):
    """
    Agrega órdenes cuya demanda está altamente cubierta por ítems comunes ya disponibles en stock.

    Ideal para aumentar la eficiencia sin necesidad de nuevos corredores, rápida y conservadora.
    """
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()
        stock = solucion.stock_seleccionado

        # Órdenes disponibles (no seleccionadas)
        ordenes_disponibles = [
            o for o in solucion.instance.orders
            if o.index not in solucion.id_selected_orders
        ]

        if not ordenes_disponibles:
            return solucion

        # Métrica de concentración: proporción de ítems cubiertos por el stock actual
        def concentracion_stock_comun(orden):
            cubiertos = sum(
                min(stock.get(i, 0), q)
                for i, q in orden.items.items()
            )
            return cubiertos / (orden.total_units + 1e-5)

        ordenes_disponibles.sort(key=concentracion_stock_comun, reverse=True)

        # Seleccionamos 1 o 2 con mejor concentración
        to_add = ordenes_disponibles[:min(2, len(ordenes_disponibles))]
        solucion.selected_orders.extend(to_add)
        solucion.id_selected_orders.update(o.index for o in to_add)

        solucion.actualizar_atributos()
        return solucion
   
class LL_agregar_monoitems_faciles(LowLevels):
    '''
    Agrega órdenes con un solo ítem cuya demanda está completamente cubierta por el stock actual.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        stock = solucion.stock_seleccionado

        # Órdenes no seleccionadas
        ordenes_disponibles = [
            orden for orden in solucion.instance.orders
            if orden.index not in solucion.id_selected_orders
        ]

        # Buscar monoproducto y stock completamente cubierto
        ordenes_utiles = []
        for orden in ordenes_disponibles:
            if len(orden.items) == 1:
                item, cantidad = list(orden.items.items())[0]
                if stock.get(item, 0) >= cantidad:
                    ordenes_utiles.append((orden, cantidad))

        # Ordenar por mayor cantidad de unidades
        ordenes_utiles.sort(key=lambda x: x[1], reverse=True)

        if not ordenes_utiles:
            return solucion

        # Agregar 1 o 2 más útiles
        to_add = [ou[0] for ou in ordenes_utiles[:2]]
        solucion.selected_orders.extend(to_add)
        solucion.id_selected_orders.update(orden.index for orden in to_add)

        solucion.actualizar_atributos()
        return solucion
    
class LL_agregar_pasillos_monoitem_clave(LowLevels):
    '''
    Agrega pasillos con un solo ítem que está en déficit de demanda.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        # Calcular déficit de cada ítem
        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado
        deficit = {
            i: max(demanda.get(i, 0) - stock.get(i, 0), 0)
            for i in demanda
        }

        # Buscar pasillos no seleccionados con un solo ítem
        corredores_disponibles = [
            r for r in solucion.instance.runners
            if r.index not in solucion.id_selected_runners and len(r.stock) == 1
        ]

        # Evaluar su utilidad: cuánto ayudan a cubrir ítems en déficit
        corredores_utiles = []
        for r in corredores_disponibles:
            item, cantidad = list(r.stock.items())[0]
            utilidad = min(cantidad, deficit.get(item, 0))
            if utilidad > 0:
                corredores_utiles.append((r, utilidad))

        # Ordenar por mayor utilidad
        corredores_utiles.sort(key=lambda x: x[1], reverse=True)

        if not corredores_utiles:
            return solucion

        # Agregar uno o dos corredores más útiles
        to_add = [r[0] for r in corredores_utiles[:2]]
        solucion.selected_runners.extend(to_add)
        solucion.id_selected_runners.update(r.index for r in to_add)

        solucion.actualizar_atributos()
        return solucion

class LL_eliminar_pasillos_monoitem_ineficientes(LowLevels):
    '''
    Elimina corredores que tienen un solo ítem y cuya utilidad en cubrir demanda es baja.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        demanda = solucion.demanda_ordenes_selecccionadas

        # Identificar corredores con un solo ítem
        corredores_mono = [
            runner for runner in solucion.selected_runners
            if len(runner.stock) == 1
        ]

        # Evaluar su utilidad: cuánto cubren la demanda real
        corredores_bajos = []
        for runner in corredores_mono:
            item, cantidad = list(runner.stock.items())[0]
            utilidad = min(cantidad, demanda.get(item, 0))
            corredores_bajos.append((runner, utilidad))

        # Ordenar por menor utilidad
        corredores_bajos.sort(key=lambda x: x[1])

        if not corredores_bajos:
            return solucion

        # Eliminar uno o dos corredores poco útiles
        to_remove = [c[0] for c in corredores_bajos[:2]]
        for corredor in to_remove:
            solucion.selected_runners.remove(corredor)
            solucion.id_selected_runners.discard(corredor.index)

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
        tiempo_inicio = time.time()

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
            if time.time() - tiempo_inicio > 2:
                    break
            id_runners_seleccionados.append(runner.index)



        #vemos las ordenes con más items
        sorted_orders = sorted(ordenes_no_seleccionadas, key=lambda r: r.total_units, reverse= True)
        
        # Seleccionar n pasillos al azar
        ordenes_agregar = sorted_orders[0:]
        
        # Agregar ids de los nuevos pasillos
        for order in ordenes_agregar:
            if time.time() - tiempo_inicio > 2:
                    break
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
    
class LL_agregacion_demandas_prioritarias(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua):
        # Crear una copia de la solución actual
        solucion = copy.deepcopy(solucion_antigua)
        instance = solucion.instance

        # Definir límite de tiempo para la ejecución
        tiempo_limite = 2  # segundos
        tiempo_inicio = time.time()

        total_items_runners = {}
        index_items_runners = {}

        # Construir diccionarios:
        # total_items_runners -> total de cada ítem en los corredores
        # index_items_runners -> corredores que contienen cada ítem
        for runner in instance.runners:
            for item_id, cantidad in runner.stock.items():
                total_items_runners[item_id] = total_items_runners.get(item_id, 0) + cantidad
                if item_id not in index_items_runners:
                    index_items_runners[item_id] = set()
                index_items_runners[item_id].add(runner.index)

        # Seleccionar una proporción aleatoria de órdenes no seleccionadas
        p = (instance.lb + 1) / instance.ub
        ordenes_disponibles = [o for o in instance.orders if o.index not in solucion.id_selected_orders]
        n = max(1, int(p * len(ordenes_disponibles)))
        n = min(n, len(ordenes_disponibles))  # Evita error si n > disponibles
        ordenes_muestra = random.sample(ordenes_disponibles, n)

        # Ordenar las órdenes seleccionadas por cantidad de unidades (descendente)
        ordenes_muestra.sort(key=lambda o: o.total_units, reverse=True)

        # Inicializar listas de seguimiento
        ordenes_agregadas = []
        corredores_agregados = set(solucion.id_selected_runners)

        # Iterar sobre cada orden en la muestra
        for orden in ordenes_muestra:
            if time.time() - tiempo_inicio > tiempo_limite:
                break

            # Identificar el ítem con mayor demanda en la orden
            item_mayor = max(orden.items.items(), key=lambda x: x[1])[0]

            # Buscar todas las órdenes que contienen ese ítem
            ordenes_con_item = [o for o in ordenes_disponibles if item_mayor in o.items]

            for o in ordenes_con_item:
                if o.index in solucion.id_selected_orders:
                    continue
                # Agregar la orden a la solución
                solucion.selected_orders.append(o)
                solucion.id_selected_orders.add(o.index)
                ordenes_agregadas.append(o)

                # Agregar los corredores que contienen los ítems requeridos por la orden
                for item in o.items:
                    if item in index_items_runners:
                        for runner_id in index_items_runners[item]:
                            if runner_id not in solucion.id_selected_runners:
                                solucion.selected_runners.append(instance.runners[runner_id])
                                solucion.id_selected_runners.add(runner_id)
                                corredores_agregados.add(runner_id)

                # Actualizar los atributos de la solución
                solucion.actualizar_atributos()

                # Evaluar si la razón unidades/pasillos está decreciendo
                unidades = solucion.total_units_orders
                pasillos = max(1, solucion.num_runners)
                ratio = unidades / pasillos
                if len(ordenes_agregadas) > 1:
                    unidades_previas = sum(o.total_units for o in ordenes_agregadas[:-1])
                    pasillos_previos = max(1, len(corredores_agregados))
                    ratio_anterior = unidades_previas / pasillos_previos
                    if ratio < ratio_anterior:
                        break  # detener si la eficiencia disminuye

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
    
class LL_swap_pasillo_ineficiente_por_util(LowLevels):
    '''
    Reemplaza un pasillo con baja utilidad por uno que aporta más a la demanda insatisfecha.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()

        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado

        # Identificar pasillo seleccionado con menor utilidad (respecto a demanda)
        def utilidad(runner):
            return sum(min(runner.stock.get(i, 0), demanda.get(i, 0)) for i in runner.stock)

        corredores_actuales = solucion.selected_runners
        if not corredores_actuales:
            return solucion

        corredores_actuales.sort(key=utilidad)
        corredor_a_remover = corredores_actuales[0]

        solucion.selected_runners.remove(corredor_a_remover)
        solucion.id_selected_runners.discard(corredor_a_remover.index)
        solucion.actualizar_atributos()

        # Buscar mejor pasillo no seleccionado que aporte más
        corredores_disponibles = [
            r for r in solucion.instance.runners
            if r.index not in solucion.id_selected_runners
        ]

        if not corredores_disponibles:
            return solucion

        corredores_disponibles.sort(key=utilidad, reverse=True)
        corredor_a_agregar = corredores_disponibles[0]

        solucion.selected_runners.append(corredor_a_agregar)
        solucion.id_selected_runners.add(corredor_a_agregar.index)
        solucion.actualizar_atributos()

        return solucion

class LL_swap_orden_random_por_facil(LowLevels):
    '''
    Reemplaza una orden al azar por otra que ya está mayormente cubierta por el stock.
    '''
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()
        stock = solucion.stock_seleccionado

        if not solucion.selected_orders:
            return solucion

        # Eliminar orden al azar
        orden_a_remover = random.choice(solucion.selected_orders)
        solucion.selected_orders.remove(orden_a_remover)
        solucion.id_selected_orders.discard(orden_a_remover.index)
        solucion.actualizar_atributos()

        # Buscar orden fácil de cubrir
        ordenes_disponibles = [
            orden for orden in solucion.instance.orders
            if orden.index not in solucion.id_selected_orders
        ]

        def cobertura(orden):
            return sum(
                min(stock.get(i, 0), q)
                for i, q in orden.items.items()
            ) / (orden.total_units + 1e-5)

        ordenes_disponibles.sort(key=cobertura, reverse=True)

        for orden in ordenes_disponibles:
            solucion.selected_orders.append(orden)
            solucion.id_selected_orders.add(orden.index)
            solucion.actualizar_atributos()
            break

        return solucion

class LL_swap_k_pasillos_ineficientes_por_utiles(LowLevels):
    '''
    Reemplaza los k pasillos menos útiles por los k más útiles, limitado a 2 segundos.
    '''
    def __init__(self, id, k=3):
        super().__init__(id)
        self.k = k

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        t0 = time.time()
        solucion = solucion_antigua.clone()
        demanda = solucion.demanda_ordenes_selecccionadas

        def utilidad(runner):
            return sum(min(runner.stock.get(i, 0), demanda.get(i, 0)) for i in runner.stock)

        if len(solucion.selected_runners) <= self.k:
            return solucion

        # Buscar pasillos menos útiles
        menos_utiles = heapq.nsmallest(self.k, solucion.selected_runners, key=utilidad)
        for corredor in menos_utiles:
            solucion.selected_runners.remove(corredor)
            solucion.id_selected_runners.discard(corredor.index)

        solucion.actualizar_atributos()

        if time.time() - t0 > 2:
            return solucion

        # Buscar candidatos útiles
        demanda = solucion.demanda_ordenes_selecccionadas
        candidatos = [
            r for r in solucion.instance.runners
            if r.index not in solucion.id_selected_runners
        ]

        mejores = heapq.nlargest(self.k, candidatos, key=utilidad)
        for corredor in mejores:
            if time.time() - t0 > 2:
                break
            solucion.selected_runners.append(corredor)
            solucion.id_selected_runners.add(corredor.index)

        solucion.actualizar_atributos()
        return solucion
    
class LL_swap_k_ordenes_daninas_por_faciles(LowLevels):
    '''
    Reemplaza k órdenes conflictivas por otras que son fáciles de cubrir, limitado a 2 segundos.
    '''
    def __init__(self, id, k=3):
        super().__init__(id)
        self.k = k

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        t0 = time.time()
        solucion = solucion_antigua.clone()
        stock = solucion.stock_seleccionado

        def dano(orden):
            return sum(max(0, q - stock.get(i, 0)) for i, q in orden.items.items())

        if len(solucion.selected_orders) <= self.k:
            return solucion

        peores = heapq.nlargest(self.k, solucion.selected_orders, key=dano)
        for orden in peores:
            solucion.selected_orders.remove(orden)
            solucion.id_selected_orders.discard(orden.index)

        solucion.actualizar_atributos()
        stock = solucion.stock_seleccionado

        if time.time() - t0 > 2:
            return solucion

        ordenes_disponibles = [
            orden for orden in solucion.instance.orders
            if orden.index not in solucion.id_selected_orders
        ]

        def cobertura(orden):
            return sum(min(stock.get(i, 0), q) for i, q in orden.items.items()) / (orden.total_units + 1e-5)

        mejores = heapq.nlargest(self.k, ordenes_disponibles, key=cobertura)
        for orden in mejores:
            if time.time() - t0 > 2:
                break
            solucion.selected_orders.append(orden)
            solucion.id_selected_orders.add(orden.index)

        solucion.actualizar_atributos()
        return solucion

class LL_swap_orden_danina_por_facil(LowLevels):
    """
    Reemplaza la orden más conflictiva (aquella que genera más exceso de demanda) por una orden 
    que ya está casi completamente cubierta por el stock actual.

    Rápida y eficaz incluso en instancias grandes, ya que analiza solo una orden por swap.
    """
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()

        if solucion.num_orders == 0:
            return solucion

        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado

        # Exceso por ítem
        exceso = {i: max(demanda[i] - stock.get(i, 0), 0) for i in demanda}

        # Medida de conflicto de una orden: cuánto suma al exceso
        def contribucion_al_exceso(order):
            return sum(min(q, exceso.get(i, 0)) for i, q in order.items.items())

        ordenes_ordenadas = sorted(solucion.selected_orders, key=contribucion_al_exceso, reverse=True)
        orden_a_eliminar = ordenes_ordenadas[0]

        solucion.selected_orders.remove(orden_a_eliminar)
        solucion.id_selected_orders.discard(orden_a_eliminar.index)
        solucion.actualizar_atributos()

        stock_actual = solucion.stock_seleccionado

        # Seleccionar orden "fácil" (alta cobertura por stock actual)
        ordenes_disponibles = [
            o for o in solucion.instance.orders if o.index not in solucion.id_selected_orders
        ]

        def cobertura(order):
            return sum(min(stock_actual.get(i, 0), q) for i, q in order.items.items()) / (order.total_units + 1e-5)

        ordenes_disponibles.sort(key=cobertura, reverse=True)

        for orden in ordenes_disponibles:
            solucion.selected_orders.append(orden)
            solucion.id_selected_orders.add(orden.index)
            solucion.actualizar_atributos()
            break  # Solo una

        return solucion

class LL_swap_runner_inutil_por_util(LowLevels):
    """
    Reemplaza un pasillo seleccionado que aporta poco a la cobertura de demanda por uno no seleccionado 
    que ayuda más a cubrir ítems con déficit.

    Selección basada en utilidad marginal. Escalable a grandes volúmenes.
    """
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()

        if solucion.num_runners == 0:
            return solucion

        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado
        deficit = {i: max(demanda[i] - stock.get(i, 0), 0) for i in demanda}

        # Utilidad marginal: cuánto ayuda a cubrir el déficit
        def utilidad_runner(runner):
            return sum(min(deficit.get(i, 0), q) for i, q in runner.stock.items())

        corredores_ordenados = sorted(solucion.selected_runners, key=utilidad_runner)
        corredor_a_eliminar = corredores_ordenados[0]

        solucion.selected_runners.remove(corredor_a_eliminar)
        solucion.id_selected_runners.discard(corredor_a_eliminar.index)
        solucion.actualizar_atributos()

        # Evaluar corredores no seleccionados
        candidatos = [
            r for r in solucion.instance.runners
            if r.index not in solucion.id_selected_runners
        ]
        candidatos.sort(key=utilidad_runner, reverse=True)

        for corredor in candidatos:
            solucion.selected_runners.append(corredor)
            solucion.id_selected_runners.add(corredor.index)
            solucion.actualizar_atributos()
            break  # Solo uno

        return solucion

class LL_dinkelbach_un_iter(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua = Solucion):
        num_it = random.randint(1,20)
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
        modelo_base.setParam('TimeLimit', num_it)
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

class LL_fuerza_bruta_un_largo(LowLevels):
    """
    Constructora que maximiza unidades recolectadas por un número dinámico de pasillos,
    determinado a partir de una solución previa. Evita repetir valores ya probados.
    Ya no integra corte anticipado vía callback.
    """

    def __init__(self, id: int):
        super().__init__(id)
        self.pasillos_usados_por_instancia = {}
        self.instance_name = ""

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        from gurobipy import GRB, Model, quicksum

        instancia = solucion_antigua.instance
        instancia_id = self.instance_name

        if instancia_id not in self.pasillos_usados_por_instancia:
            self.pasillos_usados_por_instancia[instancia_id] = set()
        pasillos_usados = self.pasillos_usados_por_instancia[instancia_id]

        total_pasillos_disponibles = len(instancia.runners)
        pasillos_actuales = solucion_antigua.num_runners

        if pasillos_usados:
            usados_menores = [k for k in range(1, pasillos_actuales) if k in pasillos_usados]
            usados_mayores = [k for k in range(pasillos_actuales + 1, total_pasillos_disponibles + 1) if k in pasillos_usados]
        else:
            usados_menores = [0]
            usados_mayores = [pasillos_actuales]

        umbral_menor = max(usados_menores if usados_menores else [0])
        umbral_mayor = min(usados_mayores if usados_mayores else [total_pasillos_disponibles])

        candidatos_primeros = [k for k in range(umbral_menor + 1, umbral_mayor + 1) if k < pasillos_actuales and k not in pasillos_usados]
        if not candidatos_primeros:
            candidatos_primeros = [k for k in range(umbral_menor + 1, umbral_mayor) if k > pasillos_actuales and k not in pasillos_usados]

            if not candidatos_primeros:
                usados_ordenados = sorted(pasillos_usados)
                intermedios = []
                for i in range(len(usados_ordenados) - 1):
                    a, b = usados_ordenados[i], usados_ordenados[i + 1]
                    for k in range(a + 1, b):
                        if k not in pasillos_usados:
                            intermedios.append(k)

                if intermedios:
                    candidatos_primeros = [min(intermedios, key=lambda x: abs(x - pasillos_actuales))]
                else:
                    candidatos_primeros = [k for k in range(1, total_pasillos_disponibles + 1) if k not in pasillos_usados]
                    if not candidatos_primeros:
                        print("Ya no hay más cantidades que recorrer")
                        return solucion_antigua

        print("Pasillos actuales:", pasillos_actuales, "| Rango de elección:", [candidatos_primeros[0], candidatos_primeros[-1]],
              "| usados:", pasillos_usados, "| instancia:", self.instance_name)
        num_pasillos = random.choice(candidatos_primeros)
        pasillos_usados.add(num_pasillos)

        orders = instancia.orders
        runners = instancia.runners
        lb = instancia.lb
        ub = instancia.ub

        I = set(i for order in orders for i in order.items.keys())
        O = {o.index for o in orders}
        A = {a.index for a in runners}
        order_dict = {o.index: o for o in orders}
        runner_dict = {a.index: a for a in runners}

        modelo = Model("Constructiva_dinamica_por_num_pasillos")
        modelo.setParam('OutputFlag', 0)
        modelo.setParam('TimeLimit', 70)
        modelo.setParam('presolve', 1)

        x = modelo.addVars(O, vtype=GRB.BINARY, name="x")
        y = modelo.addVars(A, vtype=GRB.BINARY, name="y")

        restricciones_i = {i: [] for i in I}
        for o in O:
            for i, val in order_dict[o].items.items():
                restricciones_i[i].append((o, val))

        rhs_i = {i: [] for i in I}
        for a in A:
            for i, val in runner_dict[a].stock.items():
                rhs_i[i].append((a, val))

        modelo.addConstr(quicksum(y[a] for a in A) <= num_pasillos, name="limite_pasillos")

        for i in I:
            lhs = quicksum(val * x[o] for o, val in restricciones_i[i])
            rhs = quicksum(val * y[a] for a, val in rhs_i[i])
            modelo.addConstr(lhs <= rhs, name=f"stock_{i}")

        modelo.addConstr(quicksum(order_dict[o].total_units * x[o] for o in O) <= ub, name="upper_bound")
        modelo.addConstr(quicksum(order_dict[o].total_units * x[o] for o in O) >= lb, name="lower_bound")

        modelo.setObjective(quicksum(order_dict[o].total_units * x[o] for o in O) / num_pasillos, GRB.MAXIMIZE)

        start = time.time()
        modelo.optimize()
        end = time.time()
        print(f"Tiempo real: {end - start:.2f} segundos | pasillos intentados: {num_pasillos}")

        if modelo.SolCount == 0:
            print("Modelo infactible o sin solución en el tiempo límite")
            return Solucion([], [], instancia)

        ordenes = [order_dict[o] for o in O if x[o].X > 0.5]
        corredores = [runner_dict[a] for a in A if y[a].X > 0.5]

        nueva_solucion = Solucion(
            selected_orders=ordenes,
            selected_runners=corredores,
            instance=instancia
        )

        if nueva_solucion.objective_value > solucion_antigua.objective_value:
            print(f"Nueva mejor solución {nueva_solucion.objective_value} con {num_pasillos} pasillos")
        else:
            print(f"Solución con {num_pasillos} pasillos no mejora la anterior")

        return nueva_solucion if nueva_solucion.objective_value > solucion_antigua.objective_value else solucion_antigua
