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

class LL_agregacion_ordenes_random(LowLevels):
    '''Agrega el 5% de las ordenes no seleccionadas de forma random'''
    def __init__(self, id: int):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        '''
        Algoritmo que agrega n órdenes a la solución actual.
        '''
        tiempo_inicial = time.time()

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

class LL_agregar_orden_concentrada_y_pasillos_requeridos(LowLevels):
    """
    Agrega una orden que tenga pocos tipos de ítems pero muchas unidades, priorizando eficiencia.
    Solo se agregan corredores si la demanda de la orden no está cubierta por el stock actual.
    """
    def __init__(self, id):
        super().__init__(id)

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:
        solucion = solucion_antigua.clone()
        stock = solucion.stock_seleccionado
        instance = solucion.instance

        # Buscar órdenes no seleccionadas
        ordenes_disponibles = [
            o for o in instance.orders
            if o.index not in solucion.id_selected_orders
        ]

        if not ordenes_disponibles:
            return solucion

        # Ordenar por: pocos tipos de ítems (len) y muchas unidades (total_units)
        ordenes_disponibles.sort(key=lambda o: (len(o.items), -o.total_units))

        # Seleccionar la mejor candidata bajo ese criterio
        orden_elegida = ordenes_disponibles[0]

        # Agregar orden a la solución
        solucion.selected_orders.append(orden_elegida)
        solucion.id_selected_orders.add(orden_elegida.index)
        solucion.actualizar_atributos()

        # Verificamos si hay ítems cuya demanda no está satisfecha con el stock actual
        demanda = solucion.demanda_ordenes_selecccionadas
        stock = solucion.stock_seleccionado
        deficit_items = {
            i: max(demanda[i] - stock.get(i, 0), 0)
            for i in orden_elegida.items
            if demanda[i] > stock.get(i, 0)
        }

        if not deficit_items:
            return solucion  # No se requiere agregar pasillos

        # Buscar corredores útiles no seleccionados para cubrir ítems en déficit
        corredores_disponibles = [
            r for r in instance.runners if r.index not in solucion.id_selected_runners
        ]

        corredores_utiles = []
        for corredor in corredores_disponibles:
            utilidad = sum(
                min(deficit_items.get(i, 0), q)
                for i, q in corredor.stock.items()
                if i in deficit_items
            )
            if utilidad > 0:
                corredores_utiles.append((corredor, utilidad))

        # Ordenar por mayor utilidad
        corredores_utiles.sort(key=lambda x: x[1], reverse=True)

        # Agregar solo los necesarios (máximo 2 como precaución de eficiencia)
        for corredor, _ in corredores_utiles[:2]:
            solucion.selected_runners.append(corredor)
            solucion.id_selected_runners.add(corredor.index)
            solucion.actualizar_atributos()

            # Recalcular demanda y stock por si ya está cubierto
            demanda = solucion.demanda_ordenes_selecccionadas
            stock = solucion.stock_seleccionado
            if all(stock[i] >= demanda[i] for i in deficit_items):
                break

        return solucion

class LL_dinkelbach_un_iter(LowLevels):
    def __init__(self, id):
        super().__init__(id)
        self.q_usados_por_instancia = {}
        self.instance_name = ""

    def implementacion(self, solucion_antigua = Solucion):
        instancia_id = self.instance_name
        if instancia_id not in self.q_usados_por_instancia:
            self.q_usados_por_instancia[instancia_id] = set()
            
        num_it = random.randint(1,20)
        solucion_copia = solucion_antigua.clone()
        instance = solucion_copia.instance
        
        q = solucion_copia.objective_value
        
        if q in self.q_usados_por_instancia[instancia_id]:
            print("q =", q, "ya fue usado.")
            return solucion_antigua
        else:
            self.q_usados_por_instancia[instancia_id].add(q)
        print("q actual:", q, "| q usados:", self.q_usados_por_instancia[instancia_id])
        
        orders = instance.orders
        runners = instance.runners
        lb = instance.lb
        ub = instance.ub
        I = set(i for order in orders for i in order.items.keys())
        O = {o.index for o in orders}
        A = {a.index for a in runners}
        order_dict = {o.index: o for o in orders}
        runner_dict = {a.index: a for a in runners}

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
    Integra corte anticipado vía 'Cutoff' y 'MIPNODE'.
    """

    def __init__(self, id: int):
        super().__init__(id)
        self.pasillos_usados_por_instancia = {}
        self.instance_name = ""
        self.tiempo_limite = None

    def implementacion(self, solucion_antigua: Solucion) -> Solucion:

        def cortar_por_bound(model, where):
            if where == GRB.Callback.MIP:
                bound = model.cbGet(GRB.Callback.MIP_OBJBND)
                if bound <= model._umbral:
                    print(f"Se aborta: Bound global actual {bound:.4f} ≤ solución anterior {model._umbral:.4f}")
                    model.terminate()
        tiempo_restante = self.tiempo_limite - time.time()
        tiempo_corrida = min([70, tiempo_restante])
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
                # Buscar valores entre pares consecutivos de usados
                usados_ordenados = sorted(pasillos_usados)
                intermedios = []
                for i in range(len(usados_ordenados) - 1):
                    a, b = usados_ordenados[i], usados_ordenados[i + 1]
                    for k in range(a + 1, b):
                        if k not in pasillos_usados:
                            intermedios.append(k)

                # Si hay intermedios, elegimos el más cercano a pasillos_actuales
                if intermedios:
                    candidatos_primeros = [min(intermedios, key=lambda x: abs(x - pasillos_actuales))]
                else:
                    # continuar con búsqueda total como fallback
                    candidatos_primeros = [k for k in range(1, total_pasillos_disponibles + 1) if k not in pasillos_usados]
                    if not candidatos_primeros:
                        print("Ya no hay más cantidades que recorrer")
                        return solucion_antigua
                    
        print("Pasillos actuales:",pasillos_actuales,"| Rango de elección:", [candidatos_primeros[0], candidatos_primeros[-1]], "| usados:", pasillos_usados, "| instancia:", self.instance_name)
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
        modelo.setParam('TimeLimit', tiempo_corrida)
        modelo.setParam('presolve', 1)
        modelo.setParam("StartNodeLimit", 1)
        
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

        modelo.addConstr(quicksum(y[a] for a in A) == num_pasillos, name="limite_pasillos")

        for i in I:
            lhs = quicksum(val * x[o] for o, val in restricciones_i[i])
            rhs = quicksum(val * y[a] for a, val in rhs_i[i])
            modelo.addConstr(lhs <= rhs, name=f"stock_{i}")

        modelo.addConstr(quicksum(order_dict[o].total_units * x[o] for o in O) <= ub, name="upper_bound")
        modelo.addConstr(quicksum(order_dict[o].total_units * x[o] for o in O) >= lb, name="lower_bound")

        modelo.setObjective(quicksum(order_dict[o].total_units * x[o] for o in O) / num_pasillos, GRB.MAXIMIZE)

        # Agregar valor de referencia para cortar el bound
        modelo._umbral = solucion_antigua.objective_value

        start = time.time()
        modelo.optimize(cortar_por_bound)
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