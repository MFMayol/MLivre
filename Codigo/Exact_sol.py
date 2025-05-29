
from data_structures import Instance, Order, Runner
from gurobipy import Model, GRB, quicksum

def exact_solution(instance: Instance) -> float:
    '''
    Descripción: Función que resuelve una instancia evaluando diferentes cantidades de corredores
    
    Args:
        instance (Instance): Instancia del problema
        
    Returns:
        mejor_ratio (float): Mejor razón unidades/corredores encontrada
    '''
    orders = instance.orders
    runners = instance.runners
    
    lb = instance.lb
    ub = instance.ub

    # Conjuntos usando índices originales
    O = {order.index for order in orders}
    A = {runner.index for runner in runners}
    
    # Conjunto de ítems
    I = set()
    for order in orders:
        I.update(order.items.keys())

    # Diccionarios para mapeo
    order_dict = {order.index: order for order in orders}
    runner_dict = {runner.index: runner for runner in runners}

    # Calcular unidades totales posibles (para referencia)
    total_units = sum(sum(order_dict[o].items.values()) for o in O)

    # Inicializar mejor solución
    mejor_ratio = 0.0
    mejor_k = 0
    mejor_unidades = 0

    # Evaluar diferentes cantidades de corredores (k)
    max_k = min(20, len(A))  # Máximo 20 corredores o todos los disponibles
    
    for k in range(1, max_k + 1):  # Comenzar desde 1 (k=0 no puede servir órdenes)
        modelo = Model(f"Modelo_k_{k}")
        
        # Variables de decisión
        x = modelo.addVars(O, vtype=GRB.BINARY, name="x_orden")
        y = modelo.addVars(A, vtype=GRB.BINARY, name="y_pasillo")

        # Restricción de stock
        modelo.addConstrs(
            (quicksum(order_dict[o].items.get(i, 0) * x[o] for o in O)
            <= 
            quicksum(runner_dict[a].stock.get(i, 0) * y[a] for a in A)
            for i in I
        ), name="restriccion_stock")

        # Restricción de número de corredores
        modelo.addConstr(quicksum(y[a] for a in A) == k, name="runners_limit")

        # Restricción de ub y lb respecto a la mínima y maxima cantidad de items que se pueden llevar
        modelo.addConstr(quicksum(x[o] * order_dict[o].items.get(i,0) for o in O for i in I) <= ub)
        modelo.addConstr(quicksum(x[o] * order_dict[o].items.get(i,0) for o in O for i in I) >= lb)


        # Función objetivo: maximizar unidades servidas
        modelo.setObjective(
            quicksum(
                order_dict[o].items.get(i, 0) * x[o] 
                for o in O 
                for i in I
            ),
            GRB.MAXIMIZE
        )
        
        modelo.setParam('OutputFlag', False)
        modelo.optimize()

        # Evaluar solución si es óptima
        if modelo.status == GRB.OPTIMAL:
            unidades_servidas = modelo.objVal
            ratio_actual = unidades_servidas / k
            
            # Actualizar mejor solución si encontramos mejor ratio
            if ratio_actual > mejor_ratio:
                mejor_ratio = ratio_actual
                mejor_k = k
                mejor_unidades = unidades_servidas
                
                # Guardar asignaciones de la mejor solución
                mejores_ordenes = [o for o in O if x[o].x > 0.5]
                mejores_corredores = [a for a in A if y[a].x > 0.5]
            
            print(f'Con pasillos {k} se alcanzan {unidades_servidas} unidades')
        # Liberar recursos del modelo
        del modelo

    # Mostrar resultados detallados
    print("\n" + "="*50)
    print("MEJOR SOLUCIÓN ENCONTRADA")
    print("="*50)
    print(f"• Corredores utilizados: {mejor_k}")
    print(f"• Unidades servidas: {mejor_unidades}")
    print(f"• Ratio (unidades/corredor): {mejor_ratio:.2f}")
    
    print("\nÓrdenes seleccionadas:")
    for o in mejores_ordenes:
        order = order_dict[o]
        print(f"  - Orden {o}: {order.items} (Total unidades: {sum(order.items.values())})")
    
    print("\nCorredores seleccionados:")
    for a in mejores_corredores:
        runner = runner_dict[a]
        print(f"  - Corredor {a}: {runner.stock} (Total stock: {sum(runner.stock.values())})")
    
    print("="*50 + "\n")
    
    return mejor_ratio