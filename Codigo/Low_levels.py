import numpy as np
from Instance import Instance
import copy, random
from Solucion import Solucion
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
        solucion = copy.deepcopy(solucion_antigua)
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
        solucion = copy.deepcopy(solucion_antigua)
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
        solucion = copy.deepcopy(solucion_antigua)
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
        solucion = copy.deepcopy(solucion_antigua)
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


class LL_eliminacion_pasillos_random(LowLevels):
    'LL eliminacion de pasillos random tomando un 10% al azar'
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua = Solucion):
        '''Implementa la low level que elimina el 5% de los pasillos seleccionados'''
        solucion = copy.deepcopy(solucion_antigua)
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
        solucion = copy.deepcopy(solucion_antigua)
        
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
        solucion = copy.deepcopy(solucion_antigua)
        
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




class LL_agregacion_pasillos_top(LowLevels):
    '''Implementación de la segunda low level de agregación'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n pasillos con la mayor cantidad de items a la solución actual.
        '''
        # Copia profunda de la solución original
        solucion = copy.deepcopy(solucion_antigua)
        
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
        solucion = copy.deepcopy(solucion_antigua)

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

class LL_agregacion_pasillo_orden_top(LowLevels):
    '''Ll que agrega el pasillo con más elementos y la orden con más elementos'''
    def __init__(self, id):
        super().__init__(id)
    def implementacion(self, solucion_antigua):
        solucion = copy.deepcopy(solucion_antigua)

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

class LL_reparacion_factibilidad(LowLevels):
    '''Low level que repara una solución infactible y la vuelve factible.
        Primero elimina ordenes hasta que la demanda de cada producto sea menor o igual a la disponibilidad, luego ve si respeta el UB y sino elimina ordenes con más productos'''
    
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        # Copia profunda para no alterar la original
        solucion = copy.deepcopy(solucion_antigua)

        # Actualizar por si los atributos no están al día
        solucion.actualizar_atributos()

        # Revisar demanda vs stock
        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado

        # Iterar sobre cada producto con exceso de demanda
        for id_prod in list(demanda.keys()):
            while demanda[id_prod] > stock.get(id_prod, 0):
                # Encontrar órdenes que pidan este producto
                ordenes_con_producto = [order for order in solucion.selected_orders if order.items.get(id_prod, 0) > 0]

                # Si no hay más órdenes para eliminar, salir
                if not ordenes_con_producto:
                    break

                # Ordenar por demanda descendente para eliminar primero las que más piden
                ordenes_con_producto.sort(key=lambda o: o.items.get(id_prod, 0), reverse=True)

                # Eliminar la orden más grande
                orden_a_eliminar = ordenes_con_producto[0]
                solucion.selected_orders.remove(orden_a_eliminar)
                solucion.id_selected_orders.discard(orden_a_eliminar.index)

                # Actualizar atributos tras eliminar
                solucion.actualizar_atributos()
                demanda = solucion.demanda_ordenes_selecccionadas
                stock = solucion.stock_seleccionado

        # Revisar si total_units_orders > UB
        while solucion.total_units_orders > solucion.instance.ub:
            if not solucion.selected_orders:
                break

            # Ordenar órdenes por unidades (descendente)
            solucion.selected_orders.sort(key=lambda o: o.total_units, reverse=True) #mayor a menor
            orden_a_eliminar = solucion.selected_orders[0]
            solucion.selected_orders.remove(orden_a_eliminar)
            solucion.id_selected_orders.discard(orden_a_eliminar.index)
            solucion.actualizar_atributos()

        # Revisar si total_units_orders < LB
        while solucion.total_units_orders < solucion.instance.lb:
            # Identificar órdenes disponibles para agregar
            ordenes_disponibles = [
                solucion.instance.orders[id_orden]
                for id_orden in solucion.instance.id_orders
                if id_orden not in solucion.id_selected_orders
            ]
            
            if not ordenes_disponibles:
                break

            # Ordenar por unidades (descendente) para subir rápido
            ordenes_disponibles.sort(key=lambda o: o.total_units, reverse=True)

            # Intentar agregar la orden más grande
            orden_a_agregar = ordenes_disponibles[0]
            solucion.selected_orders.append(orden_a_agregar)
            solucion.id_selected_orders.add(orden_a_agregar.index)
            solucion.actualizar_atributos()

            # Revisar demanda vs stock nuevamente
            demanda = solucion.demanda_ordenes_selecccionadas
            stock = solucion.stock_seleccionado

            # Si la orden genera exceso de demanda, revertir
            exceso = any(demanda[id_prod] > stock.get(id_prod, 0) for id_prod in demanda)
            if exceso:
                # Deshacer la adición
                solucion.selected_orders.remove(orden_a_agregar)
                solucion.id_selected_orders.discard(orden_a_agregar.index)
                solucion.actualizar_atributos()
                break  # No se puede agregar más

        # Por último, si sigue faltando stock, podrías intentar agregar pasillos
        # (Lo dejamos opcional para que definas tu estrategia)

        # Actualizar atributos finales
        solucion.actualizar_atributos()

        # Retornar la solución reparada
        return solucion


class LL_factibilizar_demanda(LowLevels):
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self, solucion_antigua):
        solucion = copy.deepcopy(solucion_antigua)

        if solucion.is_factible == True:
            return solucion

        # Actualizar por si los atributos no están al día
        solucion.actualizar_atributos()

        # Revisar demanda vs stock
        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado

        # Iterar sobre cada producto con exceso de demanda
        for id_prod in list(demanda.keys()):
            while demanda[id_prod] > stock.get(id_prod, 0):
                # Encontrar órdenes que pidan este producto
                ordenes_con_producto = [order for order in solucion.selected_orders if order.items.get(id_prod, 0) > 0]

                # Si no hay más órdenes para eliminar, salir
                if not ordenes_con_producto:
                    break

                # Ordenar por demanda descendente para eliminar primero las que más piden
                ordenes_con_producto.sort(key=lambda o: o.items.get(id_prod, 0), reverse=True)

                # Eliminar la orden más grande
                orden_a_eliminar = ordenes_con_producto[0]
                solucion.selected_orders.remove(orden_a_eliminar)
                solucion.id_selected_orders.discard(orden_a_eliminar.index)

                # Actualizar atributos tras eliminar
                solucion.actualizar_atributos()
                demanda = solucion.demanda_ordenes_selecccionadas
                stock = solucion.stock_seleccionado
        return solucion

class LL_factibilizar_UB(LowLevels):
    def __init__(self, id):
        super().__init__(id)
    
    def implementacion(self,solucion_antigua):
        solucion = copy.deepcopy(solucion_antigua)
        if solucion.is_factible == True:
            return solucion
        # Revisar si total_units_orders > UB
        while solucion.total_units_orders > solucion.instance.ub:
            if not solucion.selected_orders:
                break

            # Ordenar órdenes por unidades (descendente)
            solucion.selected_orders.sort(key=lambda o: o.total_units, reverse=True) #mayor a menor
            orden_a_eliminar = solucion.selected_orders[0]
            solucion.selected_orders.remove(orden_a_eliminar)
            solucion.id_selected_orders.discard(orden_a_eliminar.index)
            solucion.actualizar_atributos()
        return solucion

class LL_factibilizar_LB(LowLevels):
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self,solucion_antigua):
        solucion = copy.deepcopy(solucion_antigua)
        if solucion.is_factible == True:
            return solucion
        # Revisar si total_units_orders < LB
        while solucion.total_units_orders < solucion.instance.lb:
            # Identificar órdenes disponibles para agregar
            ordenes_disponibles = [
                solucion.instance.orders[id_orden]
                for id_orden in solucion.instance.id_orders
                if id_orden not in solucion.id_selected_orders
            ]
            
            if not ordenes_disponibles:
                break

            # Ordenar por unidades (descendente) para subir rápido
            ordenes_disponibles.sort(key=lambda o: o.total_units, reverse=True)

            # Intentar agregar la orden más grande
            orden_a_agregar = ordenes_disponibles[0]
            solucion.selected_orders.append(orden_a_agregar)
            solucion.id_selected_orders.add(orden_a_agregar.index)
            solucion.actualizar_atributos()

            # Revisar demanda vs stock nuevamente
            demanda = solucion.demanda_ordenes_selecccionadas
            stock = solucion.stock_seleccionado

            # Si la orden genera exceso de demanda, revertir
            exceso = any(demanda[id_prod] > stock.get(id_prod, 0) for id_prod in demanda)
            if exceso:
                # Deshacer la adición
                solucion.selected_orders.remove(orden_a_agregar)
                solucion.id_selected_orders.discard(orden_a_agregar.index)
                solucion.actualizar_atributos()
                break  # No se puede agregar más
        solucion.actualizar_atributos()
        return solucion