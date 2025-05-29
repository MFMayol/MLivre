from instance_reader import read_instance
from heuristics import greedy_wave_selection

def main():
    """
    Función principal que carga una instancia del problema, ejecuta la heurística golosa
    y muestra los resultados por consola.
    """
    instance = read_instance("instances/instance_0001.txt")
    orders, runners = greedy_wave_selection(instance)

    total_units = sum(order.total_units() for order in orders)
    num_runners = len(runners)

    if num_runners == 0:
        print("No se pudo generar una wave válida.")
    else:
        ratio = total_units / num_runners
        print(f"Órdenes seleccionadas: {[o.index for o in orders]}")
        print(f"Corredores utilizados: {[r.index for r in runners]}")
        print(f"Unidades totales entregadas: {total_units}")
        print(f"Número de corredores: {num_runners}")
        print(f"Razón unidades/corredores: {ratio:.2f}")

if __name__ == "__main__":
    main()
