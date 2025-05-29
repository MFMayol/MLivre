from typing import List
from data_structures import Order, Runner, Instance

def read_instance(filepath: str) -> Instance:
    """
    Lee un archivo de instancia y construye una estructura de datos que representa el problema.

    Formato del archivo:
        - Primera línea: o i a (número de órdenes, ítems y corredores)
        - Siguientes o líneas: cada una representa una orden con k (cantidad de ítems) y k pares (ítem, cantidad)
        - Siguientes a líneas: cada una representa un corredor con l (ítems disponibles) y l pares (ítem, cantidad)
        - Última línea: LB y UB (límites de unidades permitidas en la wave)

    Args:
        filepath (str): Ruta al archivo .txt que contiene la instancia.

    Returns:
        Instance: Objeto que representa toda la instancia del problema.
    """
    with open(filepath, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    o, i, a = map(int, lines[0].split())

    orders: List[Order] = []
    for j in range(1, 1 + o):
        parts = list(map(int, lines[j].split()))
        k = parts[0]
        items = {parts[n]: parts[n + 1] for n in range(1, 2 * k, 2)}
        orders.append(Order(index=j - 1, items=items))

    runners: List[Runner] = []
    for j in range(1 + o, 1 + o + a):
        parts = list(map(int, lines[j].split()))
        l = parts[0]
        stock = {parts[n]: parts[n + 1] for n in range(1, 2 * l, 2)}
        runners.append(Runner(index=j - 1 - o, stock=stock))

    lb, ub = map(int, lines[-1].split())
    return Instance(orders=orders, runners=runners, num_items=i, lb=lb, ub=ub)
