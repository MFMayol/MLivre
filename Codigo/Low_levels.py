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
    '''Implementación del nivel bajo que elimina el pasillo con menos productos.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        pasillos_seleccionados = list(solucion_antigua.id_selected_runners)

        if not pasillos_seleccionados:
            return solucion_antigua  # ⚠️ Evita error si no hay pasillos

        pasillos_seleccionados.sort(
            key=lambda p: solucion_antigua.instance.runners[p].total_units,
            reverse=True
        )

        pasillo_seleccionado = pasillos_seleccionados[-1]

        pasillos_seleccionados.remove(pasillo_seleccionado)

        solucion.id_selected_runners = tuple(pasillos_seleccionados)
        solucion.selected_runners = tuple(
            solucion.instance.runners[id_pasillo] for id_pasillo in pasillos_seleccionados
        )

        solucion.actualizar_atributos()
        return solucion


class LowLevel4(LowLevels):
    ''' Implementación del tercer nivel bajo del algoritmo de optimización que elimina un pasillo random de los ya seleccionados. '''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)
    
    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)
        pasillos_seleccionados = list(solucion.id_selected_runners)

        if not pasillos_seleccionados:
            return solucion_antigua  # ⚠️ Evita error si no hay pasillos

        id_pasillo_eliminado = np.random.choice(pasillos_seleccionados)
        pasillos_seleccionados.remove(id_pasillo_eliminado)

        solucion.id_selected_runners = tuple(pasillos_seleccionados)
        solucion.selected_runners = tuple(solucion.instance.runners[id_pasillo] for id_pasillo in pasillos_seleccionados)
        solucion.actualizar_atributos()

        return solucion


class LowLevel5(LowLevels):
    '''Implementación del nivel bajo que elimina la orden con menos productos y agrega una orden no seleccionada al azar.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        id_ordenes_seleccionadas = list(solucion.id_selected_orders)
        ordenes_seleccionadas = list(solucion.selected_orders)

        if not ordenes_seleccionadas:
            return solucion_antigua  # ⚠️ No se puede eliminar si no hay ninguna

        ordenes_seleccionadas.sort(key=lambda o: o.total_units)
        orden_a_eliminar = ordenes_seleccionadas[0]
        id_ordenes_seleccionadas.remove(orden_a_eliminar.index)

        ordenes_no_seleccionadas = [
            o for o in solucion.instance.orders if o.index not in id_ordenes_seleccionadas
        ]

        if not ordenes_no_seleccionadas:
            return solucion_antigua  # ⚠️ No se puede agregar si no hay opciones

        orden_a_agregar = np.random.choice(ordenes_no_seleccionadas)
        id_ordenes_seleccionadas.append(orden_a_agregar.index)

        solucion.id_selected_orders = tuple(id_ordenes_seleccionadas)
        solucion.selected_orders = tuple(solucion.instance.orders[o] for o in id_ordenes_seleccionadas)
        solucion.actualizar_atributos()

        return solucion


class LowLevel6(LowLevels):
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


class LowLevel7(LowLevels):
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

class LowLevel8(LowLevels):
    '''Agrega órdenes con base en el ítem más abundante (sobrante) en stock.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        r_i = {
            i: sum(r.stock.get(i, 0) for r in solucion.selected_runners) - 
               sum(o.items.get(i, 0) for o in solucion.selected_orders)
            for i in range(solucion.instance.num_items)
        }

        items_ordenados = sorted(r_i.items(), key=lambda x: -x[1])
        O_sC = [o for o in solucion.instance.orders if o.index not in solucion.id_selected_orders]

        for i, cantidad in items_ordenados:
            if cantidad <= 0:
                continue

            candidatos = [
                o for o in O_sC
                if o.items.get(i, 0) <= cantidad and o.total_units + solucion.total_units <= solucion.instance.ub
            ]
            if not candidatos:
                continue

            total_item = sum(o.items.get(i, 0) for o in candidatos)
            if total_item == 0:
                continue

            probs = [o.items.get(i, 0) / total_item for o in candidatos]
            seleccionada = np.random.choice(candidatos, p=probs)

            nueva_lista = list(solucion.id_selected_orders) + [seleccionada.index]
            solucion.id_selected_orders = tuple(nueva_lista)
            solucion.selected_orders = tuple(solucion.instance.orders[o] for o in nueva_lista)
            solucion.actualizar_atributos()
            return solucion

        return solucion_antigua

class LowLevel9(LowLevels):
    '''Intercambia la orden más grande por varias más pequeñas si caben en la solución.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        ordenes = list(solucion.selected_orders)
        orden_grande = max(ordenes, key=lambda o: sum(o.items.values()))
        capacidad_liberada = sum(orden_grande.items.values())

        ordenes_fuera = [o for o in solucion.instance.orders if o.index not in solucion.id_selected_orders]
        ordenes_fuera.sort(key=lambda o: sum(o.items.values()))

        nueva_lista = [o for o in ordenes if o != orden_grande]
        total = 0
        nuevas = []

        for o in ordenes_fuera:
            suma_o = sum(o.items.values())
            if total + suma_o <= capacidad_liberada and solucion.total_units - orden_grande.total_units + total + suma_o <= solucion.instance.ub:
                nuevas.append(o)
                total += suma_o

        if not nuevas:
            return solucion_antigua

        # Validación opcional: factibilidad de stock
        for i in range(solucion.instance.num_items):
            demanda = sum(o.items.get(i, 0) for o in nueva_lista + nuevas)
            oferta = sum(r.stock.get(i, 0) for r in solucion.selected_runners)
            if demanda > oferta:
                return solucion_antigua

        ordenes_final = nueva_lista + nuevas
        solucion.id_selected_orders = tuple(o.index for o in ordenes_final)
        solucion.selected_orders = tuple(ordenes_final)
        solucion.actualizar_atributos()
        return solucion

class LowLevel10(LowLevels):
    '''Reemplaza la orden con mayor diversidad de ítems por otras con menor diversidad.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        ordenes = list(solucion.selected_orders)
        orden_eliminar = max(ordenes, key=lambda o: len(o.items))
        ordenes_fuera = [o for o in solucion.instance.orders if o.index not in solucion.id_selected_orders]
        ordenes_fuera.sort(key=lambda o: len(o.items))

        nuevas = []
        total_items = sum(orden_eliminar.items.values())
        total_actual = solucion.total_units - orden_eliminar.total_units
        nueva_lista = [o for o in ordenes if o != orden_eliminar]

        for o in ordenes_fuera:
            if total_actual + o.total_units <= solucion.instance.ub:
                nuevas.append(o)
                total_actual += o.total_units
                # Chequear factibilidad antes de seguir
                factible = True
                for i in range(solucion.instance.num_items):
                    demanda = sum(x.items.get(i, 0) for x in nueva_lista + nuevas)
                    oferta = sum(r.stock.get(i, 0) for r in solucion.selected_runners)
                    if demanda > oferta:
                        factible = False
                        break
                if not factible:
                    nuevas.pop()
                    break

        if not nuevas:
            return solucion_antigua

        ordenes_final = nueva_lista + nuevas
        solucion.id_selected_orders = tuple(o.index for o in ordenes_final)
        solucion.selected_orders = tuple(ordenes_final)
        solucion.actualizar_atributos()
        return solucion

class LowLevel11(LowLevels):
    '''Reemplaza la orden con mayor diversidad relativa por órdenes con menor diversidad relativa.'''
    def __init__(self, id: int, nombre: str):
        super().__init__(id, nombre)

    def f(self, orden, Is):
        Io = set(orden.items.keys())
        denom = len(Is) - len(Io)
        if denom == 0:
            return 0
        return sum(orden.items.values()) / denom

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = copy.deepcopy(solucion_antigua)

        Is = set()
        for o in solucion.selected_orders:
            Is.update(o.items.keys())

        ordenes = list(solucion.selected_orders)
        orden_eliminar = max(ordenes, key=lambda o: self.f(o, Is))
        ordenes_fuera = [o for o in solucion.instance.orders if o.index not in solucion.id_selected_orders]
        ordenes_fuera.sort(key=lambda o: self.f(o, Is))

        nuevas = []
        total_actual = solucion.total_units - orden_eliminar.total_units
        nueva_lista = [o for o in ordenes if o != orden_eliminar]

        for o in ordenes_fuera:
            if total_actual + o.total_units <= solucion.instance.ub:
                nuevas.append(o)
                total_actual += o.total_units
                # Chequear factibilidad
                factible = True
                for i in range(solucion.instance.num_items):
                    demanda = sum(x.items.get(i, 0) for x in nueva_lista + nuevas)
                    oferta = sum(r.stock.get(i, 0) for r in solucion.selected_runners)
                    if demanda > oferta:
                        factible = False
                        break
                if not factible:
                    nuevas.pop()
                    break

        if not nuevas:
            return solucion_antigua

        ordenes_final = nueva_lista + nuevas
        solucion.id_selected_orders = tuple(o.index for o in ordenes_final)
        solucion.selected_orders = tuple(ordenes_final)
        solucion.actualizar_atributos()
        return solucion



