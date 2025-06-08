import numpy as np

def normalizar_probabilidades(probabilidades_no_normalizadas):
    """
    Normaliza un array de probabilidades para que su suma sea 1.

    Args:
        probabilidades_no_normalizadas (np.array): Un array NumPy de números
                                                  que representan probabilidades.
                                                  Pueden ser flotantes o enteros.

    Returns:
        np.array: El array de probabilidades normalizado.
                  Si la suma original es 0, devuelve un array de ceros.
    """
    if not isinstance(probabilidades_no_normalizadas, np.ndarray):
        raise TypeError("Las probabilidades deben ser un array de NumPy.")

    suma_total = np.sum(probabilidades_no_normalizadas)

    if suma_total == 0:
        # Si la suma es 0, no podemos dividir por 0.
        # Retornamos un array de ceros con la misma forma.
        return np.zeros_like(probabilidades_no_normalizadas, dtype=float)
    else:
        probabilidades_normalizadas = probabilidades_no_normalizadas / suma_total
        return probabilidades_normalizadas

def seleccionar_segun_probabilidad(probabilidades):
    """
    Selecciona un índice de un array de probabilidades basado en su distribución.
    Se asume que las probabilidades ya están normalizadas.

    Args:
        probabilidades (np.array): Un array NumPy de probabilidades. La suma de sus
                                   elementos debe ser 1 (o muy cercano a 1).

    Returns:
        int: El índice seleccionado aleatoriamente según las probabilidades.
    """
    if not isinstance(probabilidades, np.ndarray):
        raise TypeError("Las probabilidades deben ser un array de NumPy.")
    
    # Aquí podríamos añadir una comprobación si queremos ser muy estrictos,
    # pero la función `normalizar_probabilidades` ya se encarga de esto.
    # if not np.isclose(np.sum(probabilidades), 1.0):
    #     print(f"Advertencia: La suma de las probabilidades no es 1. Es: {np.sum(probabilidades)}")
    #     # Si llegamos aquí y no sumaran 1, np.random.choice podría fallar si la desviación es grande.

    seleccion = np.random.choice(len(probabilidades), p=probabilidades)
    return seleccion

