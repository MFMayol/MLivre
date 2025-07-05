from Instance import Instance
from Solucion import Solucion
import numpy as np
import time, random, copy
from funciones_auxiliares import seleccionar_segun_probabilidad
from Low_levels import LL_reparacion_factibilidad

class HiperHeuristica():
    '''Objeto que aplica el algoritmo'''
    def __init__(self, instancia = Instance, V = float, low_levels = list, solucion = Solucion, tiempo = int):
        self.instancia = instancia # objeto instancia
        self.V = V #
        self.low_levels = low_levels # lista con low levels
        self.n = len(self.low_levels) # int que tiene el número de low levels
        self.P = np.ones((self.n,self.n)) # Matriz de contador mejora
        self.T = np.zeros((self.n,self.n)) # Matriz transicion mejora
        self.Q = np.ones((self.n, 2)) # Matriz de contador freno
        self.S = np.zeros((self.n, 2)) # Matriz de probabilidad de freno
        self.mejor_sol = solucion
        self.candidata = self.mejor_sol
        self.solucion_temporal = self.mejor_sol
        self.secuencia = []
        self.s = instancia.ub
        #self.soluciones_factibles = []
        self.tiempo_maximo = time.time() + tiempo # minutos maximos
        self.costo_inicial = self.candidata.objective_value - self.candidata.costo_infactible()
        self.costo_mejor_solucion = self.mejor_sol.objective_value - self.mejor_sol.costo_infactible()

    def actualizar_matrices_T_S(self):
        ''' Descripción: 
        Método que actualiza las matrices 
            Args : 
            *   None
            Return : 
            *   None
            '''
        # primero inicializamos la matriz 
        for i in range(self.n):
                suma_P = sum(self.P[i])
                suma_Q = sum(self.Q[i])
                self.T[i] = self.P[i] / suma_P
                self.S[i] = self.Q[i] / suma_Q

    def implementar(self):
        #LL_r = LL_reparacion_factibilidad(id=1, nombre=1)
        self.actualizar_matrices_T_S()
        i_last = random.choice(self.low_levels)
        id_last =  i_last.id
        secuencia = []
        secuencia.append(id_last)
        
        tiempo_inicio = time.time()
        
        it = 0
        
        while self.tiempo_maximo - time.time() > 0:
            it+=1
            id_next = seleccionar_segun_probabilidad(self.T[id_last])
            secuencia.append(id_next)
            # ahora elegimos el valor u
            u_next = seleccionar_segun_probabilidad(self.S[id_last])

            if u_next == 1:
                sol_temporal = self.candidata
                for id in secuencia:
                    low_level = self.low_levels[id]
                    sol_temporal = low_level.implementacion(sol_temporal)
                
                # cambiaré esto
                #if sol_temporal.is_factible == False:
                 #   sol_temporal = LL_r.implementacion(sol_temporal)

                if  self.condicion_1(sol_temporal, self.candidata) or self.condicion_2(sol_temporal, self.mejor_sol, tiempo_inicio, self.V):
                    self.candidata = copy.deepcopy(sol_temporal)
                    for id in range(len(secuencia)-1):
                        self.P[secuencia[id], secuencia[id+1]] = self.P[secuencia[id], secuencia[id+1]] + 1
                        self.Q[secuencia[id], 0] = self.Q[secuencia[id], 0] + 1
                    self.Q[secuencia[-1], 1] = self.Q[secuencia[-1], 1] + 1
                    
                    self.actualizar_matrices_T_S()
                
                if self.condicion_1(sol_temporal, self.mejor_sol):
                    self.mejor_sol = copy.deepcopy(sol_temporal)
                
                print(f"Conteo = {it}, s_t = {sol_temporal.objective_value:.2f} {sol_temporal.is_factible}, s_c = {self.candidata.objective_value:.2f} {self.candidata.is_factible}, s* = {self.mejor_sol.objective_value:.2f} {self.mejor_sol.is_factible}, secuencia = {secuencia}") 
                secuencia = []
                
            id_last = id_next
                    
                

    def condicion_1(self, sol_temporal: Solucion, sol_candidata : Solucion):
        if sol_temporal.objective_value - 10000*sol_temporal.costo_infactible() > sol_candidata.objective_value - 10000*sol_candidata.costo_infactible():
            return True
        return False
    
    def condicion_2(self, sol_temporal: Solucion, mejor_sol: Solucion, tiempo_inicio: float, V: float):
        time_el = time.time()-tiempo_inicio #Elapsed time
        
        if mejor_sol.is_factible: #Calculo de threshold según factibilidad de mejor solución
            rho = 10**-5 + V*(1-(time_el)/self.tiempo_maximo)
        else:
            rho = 10**-3
        
        if sol_temporal.objective_value - self.s*sol_temporal.costo_infactible()  > (1 + rho)*(mejor_sol.objective_value - self.s*mejor_sol.costo_infactible()):
            return True
        return False
        
        