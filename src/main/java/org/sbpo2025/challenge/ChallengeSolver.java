package org.sbpo2025.challenge;

import org.apache.commons.lang3.time.StopWatch;

import ilog.concert.*;
import ilog.cplex.*;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;


public class ChallengeSolver {
    private final long MAX_RUNTIME = 600000; // milliseconds; 10 minutes

    // Evita repetir q en Dinkelbach (almacenado redondeado)
    private static final Set<Double> Q_USADOS_GLOBAL = new HashSet<>();

    // Memorias globales (evita repetir K de pasillos y guarda UB/infactibles)
    private static final Set<Integer> PASILLOS_USADOS = new HashSet<>();
    // Marca: forzar una sola vez la primera elección menor a p_c
    private static boolean PRIMERA_ELECCION_MENORES_HECHA = false;  
    // Memo de ordenamiento y prefijos por #items en pasillos
    private List<Integer> aislesByNumItemsAscMemo = null;
    private long[] prefixAisleSizeAsc = null; // pref[0]=0; pref[j]=sum de los j pasillos más "pequeños"
    private long sumAisleSizes = -1L;         // suma total de #items sobre todos los pasillos
    private int[] typesPerOrder = null;       // tau_o por orden

    private static final Set<Integer> PASILLOS_INFACTIBLES = new HashSet<>();
    private static final Set<Integer> PASILLOS_OBJETIVOS = new HashSet<>();

    protected List<Map<Integer, Integer>> orders;
    protected List<Map<Integer, Integer>> aisles;
    protected int nItems;      // número nominal (puede ser < max key real)
    protected int waveSizeLB;
    protected int waveSizeUB;

    public ChallengeSolver(List<Map<Integer, Integer>> orders,
                           List<Map<Integer, Integer>> aisles,
                           int nItems,
                           int waveSizeLB,
                           int waveSizeUB) {
        this.orders = orders;
        this.aisles = aisles;
        this.nItems = nItems;
        this.waveSizeLB = waveSizeLB;
        this.waveSizeUB = waveSizeUB;
    }

    public ChallengeSolution solve(StopWatch stopWatch) {
        // ===== Validaciones básicas =====
        if (stopWatch != null && !stopWatch.isStarted()) {
            stopWatch.start();
        }


        final int numOrders = orders.size();
        final int numAisles = aisles.size();
        final int N = effectiveNItems(); // usa el máximo índice real observado

        // u_o = sum_i d_{oi}
        int[] unitsPerOrder = new int[numOrders];
        for (int o = 0; o < numOrders; o++) {
            int sum = 0;
            for (int v : orders.get(o).values()) sum += v;
            unitsPerOrder[o] = sum;
        }
        // ========= Pre-ordenamiento (conjunto) por #ítems en cada Map =========
        // Mide el tiempo total de ordenar ambas colecciones.
        final long tSort0 = System.nanoTime();

        // Índices de órdenes ordenados ascendentemente por cantidad de ítems distintos
        Integer[] orderIdx = new Integer[numOrders];
        for (int o = 0; o < numOrders; o++) orderIdx[o] = o;
        Arrays.sort(orderIdx, Comparator.comparingInt(o -> orders.get(o).size()));

        // Índices de pasillos ordenados ascendentemente por cantidad de ítems distintos
        Integer[] aisleIdx = new Integer[numAisles];
        for (int a = 0; a < numAisles; a++) aisleIdx[a] = a;
        Arrays.sort(aisleIdx, Comparator.comparingInt(a -> aisles.get(a).size()));

        final long tSort1 = System.nanoTime();
        System.out.printf(
            Locale.US,
            "[Ordenamiento] %d órdenes y %d pasillos ordenados por #ítems en %.3f ms (conjunto).%n",
            numOrders, numAisles, (tSort1 - tSort0) / 1e6
        );

        // tau_o: #items distintos por orden (memo)
        typesPerOrder = new int[numOrders];
        for (int o = 0; o < numOrders; o++) typesPerOrder[o] = orders.get(o).size();

        // Prefijos por pasillos ya ordenados ascendente (aislesByNumItemsAsc)
        int NA = numAisles;
        long[] pref = new long[NA + 1]; // pref[0]=0
        long total = 0L;
        for (int j = 0; j < NA; j++) {
            int aIdx = aisleIdx[j];                 // índice real del pasillo en posición j ascendente
            int sz   = aisles.get(aIdx).size();     // #items distintos en ese pasillo
            pref[j + 1] = pref[j] + sz;
            total += sz;
        }
        // Memo disponibles para H1:
        this.aislesByNumItemsAscMemo = Collections.unmodifiableList(Arrays.asList(aisleIdx));
        this.prefixAisleSizeAsc = pref;
        this.sumAisleSizes = total;
        // Precompute sumStockAisle[a] = sum_i s_ai  (memo global del solve)
        long[] sumStockAisle = new long[numAisles];
        for (int a = 0; a < numAisles; a++) {
            long s = 0L;
            for (int v : aisles.get(a).values()) s += v;
            sumStockAisle[a] = s;
        }


        // ========= 1) CONSTRUCTORA: minimizar pasillos con cotas de unidades =========
        ChallengeSolution current;
        {
            final long t0All = System.nanoTime();
            try (IloCplex cplex = new IloCplex()) {
                // === Parámetros CPLEX ===
                cplex.setOut(null);        // apaga
                cplex.setWarning(null);    // apaga warnings de CPLEX
                cplex.setParam(IloCplex.Param.TimeLimit, 25.0);        // segundos (límite absoluto)
                cplex.setParam(IloCplex.Param.MIP.Display, 0);         // silencia log
                try { cplex.setParam(IloCplex.Param.Emphasis.MIP, 1); } catch (Throwable ignore) {}

                // ===== Preagregado esparso por ítem =====
                @SuppressWarnings("unchecked")
                ArrayList<int[]>[] demandPairs = new ArrayList[N];
                @SuppressWarnings("unchecked")
                ArrayList<int[]>[] supplyPairs = new ArrayList[N];

                for (int o = 0; o < numOrders; o++) {
                    for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                        int i = e.getKey(), qty = e.getValue();
                        if (qty == 0 || i < 0) continue;
                        if (i >= N) continue; // por seguridad
                        ArrayList<int[]> list = demandPairs[i];
                        if (list == null) { list = new ArrayList<>(); demandPairs[i] = list; }
                        list.add(new int[]{o, qty});
                    }
                }
                for (int a = 0; a < numAisles; a++) {
                    for (Map.Entry<Integer, Integer> e : aisles.get(a).entrySet()) {
                        int i = e.getKey(), stk = e.getValue();
                        if (stk == 0 || i < 0) continue;
                        if (i >= N) continue; // por seguridad
                        ArrayList<int[]> list = supplyPairs[i];
                        if (list == null) { list = new ArrayList<>(); supplyPairs[i] = list; }
                        list.add(new int[]{a, stk});
                    }
                }

                final long tBuild0 = System.nanoTime();

                // Variables
                IloNumVar[] x = cplex.boolVarArray(numOrders);  // seleccionar órdenes
                IloNumVar[] y = cplex.boolVarArray(numAisles);  // abrir pasillos

                // Restricciones de stock por ítem
                for (int i = 0; i < N; i++) {
                    ArrayList<int[]> dem = demandPairs[i];
                    if (dem == null || dem.isEmpty()) continue;

                    IloLinearNumExpr lhs = cplex.linearNumExpr();
                    for (int[] p : dem) lhs.addTerm(p[1], x[p[0]]);

                    ArrayList<int[]> sup = supplyPairs[i];
                    if (sup == null || sup.isEmpty()) {
                        cplex.addLe(lhs, 0.0);
                    } else {
                        IloLinearNumExpr rhs = cplex.linearNumExpr();
                        for (int[] p : sup) rhs.addTerm(p[1], y[p[0]]);
                        cplex.addLe(lhs, rhs);
                    }
                }

                // waveSizeLB <= sum_o u_o x_o <= waveSizeUB
                IloLinearNumExpr totalPicked = cplex.linearNumExpr();
                for (int o = 0; o < numOrders; o++) {
                    int uo = unitsPerOrder[o];
                    if (uo != 0) totalPicked.addTerm(uo, x[o]);
                }
                cplex.addGe(totalPicked, waveSizeLB);
                cplex.addLe(totalPicked, waveSizeUB);

                // === NUEVO: exigir que la suma de ítems sea al menos (LB+UB)/2 ===
                final int midBound = (int) Math.ceil((waveSizeLB + waveSizeUB) / 2.0);
                cplex.addGe(totalPicked, midBound, "mid_lower_bound");


                // Objetivo: MINIMIZAR pasillos
                IloLinearNumExpr totalVisitedAisles = cplex.linearNumExpr();
                for (int a = 0; a < numAisles; a++) totalVisitedAisles.addTerm(1.0, y[a]);
                cplex.addMinimize(totalVisitedAisles);

                final long tBuild1 = System.nanoTime();

                // SOLVE
                final long tSolve0 = System.nanoTime();
                boolean solved = cplex.solve();
                final long tSolve1 = System.nanoTime();

                if (solved) {
                    Set<Integer> selectedOrders = new HashSet<>();
                    Set<Integer> visitedAisles = new HashSet<>();

                    for (int o = 0; o < numOrders; o++) if (cplex.getValue(x[o]) > 0.5) selectedOrders.add(o);
                    for (int a = 0; a < numAisles; a++) if (cplex.getValue(y[a]) > 0.5) visitedAisles.add(a);

                    double picked = cplex.getValue(totalPicked);            // unidades
                    int    pas    = visitedAisles.size();
                    double objReal = (pas == 0) ? 0.0 : (picked / pas);     // items / pasillos
                    double gap     = Double.NaN; try { gap = cplex.getMIPRelativeGap(); } catch (Exception ignore) {}

                    double tAll   = (System.nanoTime() - t0All) / 1e9;
                    double tBuild = (tBuild1 - tBuild0) / 1e9;
                    double tSolve = (tSolve1 - tSolve0) / 1e9;

                    System.out.printf(Locale.US,
                        "Tiempo total: %.2f s | build: %.2f s | solve: %.2f s | OBJ=%.2f | Unidades=%.0f (LB=%d, UB=%d) | Pasillos=%d | GAP=%.4f | Status=%s%n",
                        tAll, tBuild, tSolve,
                        objReal, picked, waveSizeLB, waveSizeUB, pas, gap,
                        String.valueOf(cplex.getCplexStatus())
                    );

                    current = new ChallengeSolution(selectedOrders, visitedAisles);
                } else {
                    double tAll   = (System.nanoTime() - t0All) / 1e9;
                    double tBuild = (tBuild1 - tBuild0) / 1e9;
                    double tSolve = (tSolve1 - tSolve0) / 1e9;

                    System.out.printf(Locale.US,
                        "Tiempo total: %.2f s | build: %.2f s | solve: %.2f s | Status=%s%n",
                        tAll, tBuild, tSolve, String.valueOf(cplex.getCplexStatus())
                    );

                    current = new ChallengeSolution(Collections.emptySet(), Collections.emptySet());
                }
            } catch (IloException e) {
                e.printStackTrace();
                current = new ChallengeSolution(Collections.emptySet(), Collections.emptySet());
            }
        }

        // ========= 2) Bandit con dos heurísticas =========
        int T1 = 10, T2 = 10;         // T_1,0 = T_2,0 = 10
        double p1 = 0.5, p2 = 0.5;  // p_1,0 = p_2,0 = 0.5
        final Random rng = new Random();

        // helper para evaluar objetivo unidades/#pasillos
        java.util.function.ToDoubleFunction<ChallengeSolution> evalObj = sol -> {
            int A = (sol.aisles() == null) ? 0 : sol.aisles().size();
            if (A == 0) return 0.0;
            int U = 0;
            if (sol.orders() != null) {
                for (int o : sol.orders()) for (int v : orders.get(o).values()) U += v;
            }
            return ((double) U) / A;
        };

        double currentObj = evalObj.applyAsDouble(current);
        // === Seguimiento del mejor global y el tiempo en que se alcanzó ===
        double bestObjEver = currentObj;
        double tBestSec = (stopWatch != null) ? stopWatch.getTime(TimeUnit.MILLISECONDS) / 1000.0 : -1.0;


        int t = 0;
        while (getRemainingTime(stopWatch) > 1) {  // 1s de colchón
            t++;
            boolean useH1 = rng.nextDouble() < p1;
            String who = useH1 ? "H1" : "H2";

            ChallengeSolution candidate = current; // fallback seguro
            long th0 = System.nanoTime();

            if (useH1) {
                    // ------------------- h1: Fuerza bruta con callback (una corrida) -------------------
                    System.out.println("inicio ----------------------------------------------------------------------------------------------------------------");

                    // ====== Parámetros de tiempo locales ======
                    final double tiempo_restante = Math.max(1.0, (double) getRemainingTime(stopWatch));
                    final double tiempo_correr   = Math.min(85.0, Math.max(1.0, tiempo_restante - 2.0)); // 2s de colchón
                    final double tiempo_corrida  = tiempo_correr;
                    final double noIncCutoff     = Math.min(35.0, Math.max(1.0, tiempo_corrida - 1.0)); // 30s o (TL-1s)


                    // ====== Datos base ======
                    final int total_pasillos_disponibles = numAisles;
                    final int pasillos_actuales = (current != null && current.aisles() != null) ? current.aisles().size() : 0;

                    // Estados/memorias globales
                    final Set<Integer> pasillos_usados        = PASILLOS_USADOS;
                    final Set<Integer> pasillos_infactibles   = PASILLOS_INFACTIBLES;
                    final Set<Integer> pasillos_objetivos     = PASILLOS_OBJETIVOS;

                    // Info previa (para p_c)
                    final double s_estrella = currentObj;     // = unidades/pasillos de la solución antigua (baseline)
                    final int lb = waveSizeLB, ub = waveSizeUB;

                    // ---------- Heurística para escoger #pasillos a probar (num_pasillos) ----------
                    System.out.println("los máximos pasillos son: " + pasillos_objetivos);
                    // Corte UB/z* anticipado
                    final int limite_superior_pasillos = pasillos_objetivos.isEmpty()
                            ? total_pasillos_disponibles
                            : Collections.min(pasillos_objetivos);

                    if (limite_superior_pasillos < 1) {
                        System.out.println("Corte anticipado: UB/z_actual < 1 ⇒ ninguna solución es mejor.");
                        // nos quedamos con 'candidate=current' tal como está
                    } else {
                        System.out.printf(Locale.US, "No conviene usar más de %d pasillos.%n", limite_superior_pasillos);

                        // Nuevo valor crítico basado en lb / s*
                        final int p_c = (s_estrella > 0.0) ? (int) Math.floor(lb / s_estrella) : total_pasillos_disponibles;

                        // Probabilidad de buscar menores a p_c (0.25) o hacer la búsqueda original (0.75)
                        final boolean buscar_menores = rng.nextDouble() < 0.35;
                        Integer primer_forzado = null;

                        // Identificar p_inf: mayor pasillo menor a p_c que resultó infactible
                        int p_inf = 0;
                        for (int k : pasillos_infactibles) if (k < p_c + 1 && k > p_inf) p_inf = k;

                        final List<Integer> candidatos_primeros = new ArrayList<>();
                        if (buscar_menores && p_c > 1 && p_c > p_inf) {
                            // 1) Primera vez: forzar primer valor = min(p_c, 10) si es usable
                            if (!PRIMERA_ELECCION_MENORES_HECHA) {
                                final int primer = Math.min(p_c, 10);
                                final boolean dentroRango = (primer > p_inf) && (primer <= p_c);
                                final boolean usable = !pasillos_usados.contains(primer)
                                        && (primer < limite_superior_pasillos)
                                        && !pasillos_infactibles.contains(primer);

                                if (dentroRango && usable) {
                                    candidatos_primeros.add(0, primer); // asegúralo en la posición 0
                                    primer_forzado = primer;            // <<< guardar para selección determinística
                                    System.out.printf(Locale.US, "[Heurística] ✅ Primera elección forzada k=%d (min(p_c,10))%n", primer);
                                    PRIMERA_ELECCION_MENORES_HECHA = true;
                                }

                            }

                            // 2) Completar el resto de candidatos en (p_inf, p_c], evitando duplicar el "primer"
                            for (int k = p_inf + 1; k <= p_c; k++) {
                                if (!pasillos_usados.contains(k) && k < limite_superior_pasillos) {
                                    if (candidatos_primeros.isEmpty() || k != candidatos_primeros.get(0)) {
                                        candidatos_primeros.add(k);
                                    }
                                }
                            }

                            System.out.printf(Locale.US, "[Heurística] 🔽 Buscando menores a p_c=%d en rango (%d, %d)%n",
                                    p_c, p_inf + 1, p_c);
                            if (candidatos_primeros.isEmpty()) {
                                System.out.println("No quedan candidatos por revisar, continuamos de la forma original");
                            }
                        }

                        if (candidatos_primeros.isEmpty()) {
                            // Búsqueda original con umbrales
                            List<Integer> usados_menores, usados_mayores;
                            if (!pasillos_usados.isEmpty()) {
                                usados_menores = new ArrayList<>();
                                usados_mayores = new ArrayList<>();
                                for (int k = 1; k < pasillos_actuales; k++) if (pasillos_usados.contains(k)) usados_menores.add(k);
                                for (int k = pasillos_actuales + 1; k <= total_pasillos_disponibles; k++)
                                    if (pasillos_usados.contains(k)) usados_mayores.add(k);
                            } else {
                                usados_menores = Collections.singletonList(0);
                                usados_mayores = Collections.singletonList(pasillos_actuales);
                            }
                            int umbral_menor = usados_menores.isEmpty() ? 0 : Collections.max(usados_menores);
                            int umbral_mayor = usados_mayores.isEmpty() ? total_pasillos_disponibles : Collections.min(usados_mayores);

                            // primero, intentar con k < pasillos_actuales
                            for (int k = umbral_menor + 1; k <= umbral_mayor; k++) {
                                if (k < pasillos_actuales && !pasillos_usados.contains(k) && k <= limite_superior_pasillos)
                                    candidatos_primeros.add(k);
                            }
                            // si vacío, intentar con k > pasillos_actuales
                            if (candidatos_primeros.isEmpty()) {
                                for (int k = umbral_menor + 1; k < umbral_mayor; k++) {
                                    if (k > pasillos_actuales && !pasillos_usados.contains(k) && k <= limite_superior_pasillos)
                                        candidatos_primeros.add(k);
                                }
                                // si sigue vacío, tomar intermedios entre usados
                                if (candidatos_primeros.isEmpty()) {
                                    List<Integer> usados_ordenados = new ArrayList<>(pasillos_usados);
                                    Collections.sort(usados_ordenados);
                                    List<Integer> intermedios = new ArrayList<>();
                                    for (int i = 0; i + 1 < usados_ordenados.size(); i++) {
                                        int a = usados_ordenados.get(i), b = usados_ordenados.get(i + 1);
                                        for (int k = a + 1; k < b; k++) if (!pasillos_usados.contains(k)) intermedios.add(k);
                                    }
                                    if (!intermedios.isEmpty()) {
                                        // escoger el más cercano a pasillos_actuales
                                        int mejor = intermedios.get(0);
                                        int bestDist = Math.abs(mejor - pasillos_actuales);
                                        for (int v : intermedios) {
                                            int d = Math.abs(v - pasillos_actuales);
                                            if (d < bestDist) { bestDist = d; mejor = v; }
                                        }
                                        candidatos_primeros.add(mejor);
                                    } else {
                                        for (int k = 1; k <= total_pasillos_disponibles; k++) {
                                            if (!pasillos_usados.contains(k) && k <= limite_superior_pasillos) candidatos_primeros.add(k);
                                        }
                                        if (candidatos_primeros.isEmpty()) {
                                            System.out.println("Ya no hay más cantidades que recorrer");
                                            // nos quedamos con 'candidate=current'
                                        }
                                    }
                                }
                            }
                        }
                        if (pasillos_actuales > 0 && !pasillos_usados.contains(pasillos_actuales)) {
                            candidatos_primeros.add(pasillos_actuales);
                        }

                        // Elegir aleatoriamente un número de pasillos
                        Integer num_pasillos = null;
                        if (!candidatos_primeros.isEmpty()) {
                            int minC = Collections.min(candidatos_primeros), maxC = Collections.max(candidatos_primeros);
                            System.out.printf(Locale.US,
                                    "Pasillos actuales: %d | Escogiendo desde [%d, %d] | pasillos usados = %s%n",
                                    pasillos_actuales, minC, maxC, pasillos_usados.toString());
                            if (primer_forzado != null) {
                                num_pasillos = primer_forzado;  // <<< usar el forzado sí o sí
                                System.out.printf(Locale.US, "Probando (forzado) con %d pasillos%n", num_pasillos);
                            } else {
                                num_pasillos = candidatos_primeros.get(rng.nextInt(candidatos_primeros.size()));
                                System.out.printf(Locale.US, "Probando con %d pasillos%n", num_pasillos);
                            }
                            pasillos_usados.add(num_pasillos);

                        } else {
                            System.out.println("No quedan candidatos para probar.");

                            // === Fallback: probar con q distintos (Dinkelbach) generados desde q usados y k usados ===
                            // Base = currentObj; vecinos multiplicativos + puntos medios entre q usados + LB/UB por k usados
                            List<Double> qSeeds = new ArrayList<>();
                            double baseQ = (currentObj > 0.0 ? currentObj : 1.0);
                            double[] mult = {0.92, 0.98, 1.02, 1.08};
                            for (double m : mult) qSeeds.add(round6(baseQ * m));

                            // puntos medios entre q usados
                            TreeSet<Double> usedQSorted = new TreeSet<>(Q_USADOS_GLOBAL);
                            Double lastQ = null;
                            for (Double qv : usedQSorted) {
                                if (lastQ != null) qSeeds.add(round6(0.5 * (qv + lastQ)));
                                lastQ = qv;
                            }

                            // de k usados (aproxa q ~ unidades/pasillos con LB/UB)
                            for (int k : PASILLOS_USADOS) {
                                if (k > 0) {
                                    qSeeds.add(round6((double) lb / k));
                                    qSeeds.add(round6((double) ub / k));
                                }
                            }

                            // filtra duplicados, <=0 y q ya usados
                            LinkedHashSet<Double> uniq = new LinkedHashSet<>();
                            for (double q : qSeeds) if (q > 0.0 && !Q_USADOS_GLOBAL.contains(q)) uniq.add(q);
                            qSeeds = new ArrayList<>(uniq);

                            // si aún vacío, fuerza un par alrededor de baseQ
                            if (qSeeds.isEmpty()) {
                                qSeeds.add(round6(baseQ * 0.95));
                                qSeeds.add(round6(baseQ * 1.05));
                            }

                            System.out.println("[Fallback@H1] Sin k nuevos: pruebo Dinkelbach con q seeds = " + qSeeds);

                            // Presupuesto de tiempo por q (con colchón y límite razonable por intento)
                            double resto = Math.max(1.0, (double) getRemainingTime(stopWatch));
                            double perTL = Math.min(15.0, Math.max(1.0, resto - 1.0));

                            for (double qTry : qSeeds) {
                                if (getRemainingTime(stopWatch) <= 1) break; // respeta MAX_RUNTIME
                                Q_USADOS_GLOBAL.add(qTry);

                                ChallengeSolution solQ = runDinkelbachWithQ(qTry, perTL, unitsPerOrder, N);
                                if (solQ != null) {
                                    double valCand = evalObj.applyAsDouble(solQ);
                                    double valBest = evalObj.applyAsDouble(candidate);
                                    if (valCand > valBest) {
                                        candidate = solQ;
                                        System.out.printf(Locale.US, "[Fallback@H1] Mejoró con q=%.4f -> obj=%.4f%n", qTry, valCand);
                                    } else {
                                        System.out.printf(Locale.US, "[Fallback@H1] q=%.4f no mejora (obj=%.4f).%n", qTry, valCand);
                                    }
                                } else {
                                    System.out.printf(Locale.US, "[Fallback@H1] q=%.4f sin solución en %.1fs.%n", qTry, perTL);
                                }
                            }
                            // fin fallback q
                        }


                        if (num_pasillos != null) {
                            // ====== MODELO CPLEX ======
                            try (IloCplex cpx = new IloCplex()) {
                                cpx.setOut(null);        // apaga TODO el log de CPLEX
                                cpx.setWarning(null);    // apaga warnings de CPLEX
                                cpx.setParam(IloCplex.Param.MIP.Display, 0);

                                cpx.setParam(IloCplex.Param.TimeLimit, tiempo_corrida); // ~80s o (restante-2s)
                                // === Frecuencia de callback (opcional pero útil) ===
                                try { cpx.setParam(IloCplex.Param.MIP.Interval, 1); } catch (Throwable __) {}

                                // === Watchdog: abortar si no hay incumbente tras noIncCutoff segundos ===
                                final IloCplex.Aborter aborter = new IloCplex.Aborter();
                                cpx.use(aborter);
                                final AtomicBoolean hayIncumbente = new AtomicBoolean(false);
                                final Timer watchdog = new Timer(true);
                                watchdog.schedule(new TimerTask() {
                                    @Override public void run() {
                                        if (!hayIncumbente.get()) {
                                            System.out.printf(Locale.US, "[Watchdog] %.0fs sin incumbente → abort()%n", noIncCutoff);
                                            aborter.abort();
                                        }
                                    }
                                }, (long) Math.ceil(noIncCutoff * 1000.0));


                                try { cpx.setParam(IloCplex.Param.Threads, 1); } catch (Throwable __) {}
                                try { cpx.setParam(IloCplex.Param.Preprocessing.Presolve, true); } catch (Throwable __) {}

                                // Variables
                                IloNumVar[] xVar = cpx.boolVarArray(numOrders); // x_o
                                IloNumVar[] yVar = cpx.boolVarArray(numAisles); // y_a

                                // Igualdad: #pasillos
                                {
                                    IloLinearNumExpr sumY = cpx.linearNumExpr();
                                    for (int a = 0; a < numAisles; a++) sumY.addTerm(1.0, yVar[a]);
                                    cpx.addEq(sumY, num_pasillos, "limite_pasillos");
                                }

                                // Preconstruir listas por ítem (restricciones_i y rhs_i)
                                @SuppressWarnings("unchecked")
                                ArrayList<int[]>[] restricciones_i = new ArrayList[N];
                                @SuppressWarnings("unchecked")
                                ArrayList<int[]>[] rhs_i = new ArrayList[N];

                                for (int o = 0; o < numOrders; o++) {
                                    for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                                        int i = e.getKey(), val = e.getValue();
                                        if (val <= 0 || i < 0 || i >= N) continue;
                                        if (restricciones_i[i] == null) restricciones_i[i] = new ArrayList<>();
                                        restricciones_i[i].add(new int[]{o, val});
                                    }
                                }
                                for (int a = 0; a < numAisles; a++) {
                                    for (Map.Entry<Integer, Integer> e : aisles.get(a).entrySet()) {
                                        int i = e.getKey(), val = e.getValue();
                                        if (val <= 0 || i < 0 || i >= N) continue;
                                        if (rhs_i[i] == null) rhs_i[i] = new ArrayList<>();
                                        rhs_i[i].add(new int[]{a, val});
                                    }
                                }

                                // Stock por ítem
                                for (int i = 0; i < N; i++) {
                                    ArrayList<int[]> L = restricciones_i[i];
                                    if (L == null || L.isEmpty()) continue;
                                    IloLinearNumExpr lhs = cpx.linearNumExpr();
                                    for (int[] p : L) lhs.addTerm(p[1], xVar[p[0]]);

                                    ArrayList<int[]> R = rhs_i[i];
                                    if (R == null || R.isEmpty()) {
                                        cpx.addLe(lhs, 0.0, "stock_" + i);
                                    } else {
                                        IloLinearNumExpr rhs = cpx.linearNumExpr();
                                        for (int[] p : R) rhs.addTerm(p[1], yVar[p[0]]);
                                        cpx.addLe(lhs, rhs, "stock_" + i);
                                    }
                                }

                                // Cotas LB/UB en unidades
                                IloLinearNumExpr totalUnits = cpx.linearNumExpr();
                                for (int o = 0; o < numOrders; o++) {
                                    int uo = unitsPerOrder[o];
                                    if (uo != 0) totalUnits.addTerm(uo, xVar[o]);
                                }
                                cpx.addLe(totalUnits, ub, "upper_bound");
                                cpx.addGe(totalUnits, lb, "lower_bound");

                                // Objetivo: maximizar (sum u_o x_o) / num_pasillos
                                IloNumExpr obj = cpx.prod(1.0 / Math.max(1, num_pasillos), totalUnits);
                                cpx.addMaximize(obj);

                                // ===== Greedy inicial con k = num_pasillos (MIP start) =====
                                {
                                    final long g0 = System.nanoTime();

                                    final int kG = Math.min(num_pasillos, numAisles);
                                    if (kG <= 0) {
                                        System.out.println("[Greedy] k<=0, omito MIP start.");
                                    } else {
                                        long lbTypesG = 0L, ubTypesG = Long.MAX_VALUE;
                                        boolean haveTypeBoundsG = false;
                                        if (prefixAisleSizeAsc != null && prefixAisleSizeAsc.length == numAisles + 1 && sumAisleSizes >= 0L) {
                                            int NA_local = numAisles;
                                            int kk = Math.min(Math.max(kG, 0), NA_local);
                                            lbTypesG = prefixAisleSizeAsc[kk];
                                            ubTypesG = sumAisleSizes - prefixAisleSizeAsc[NA_local - kk];
                                            haveTypeBoundsG = true;
                                        }

                                        // elegir kG pasillos: top-k por stock total (desempate: más tipos)
                                        Integer[] aisleOrderByScore = new Integer[numAisles];
                                        for (int a = 0; a < numAisles; a++) aisleOrderByScore[a] = a;
                                        Arrays.sort(aisleOrderByScore, (a, b) -> {
                                            int cmp = Long.compare(sumStockAisle[b], sumStockAisle[a]); // desc
                                            if (cmp != 0) return cmp;
                                            return Integer.compare(aisles.get(b).size(), aisles.get(a).size());
                                        });
                                        Set<Integer> greedyAisles = new HashSet<>(kG);
                                        for (int j = 0; j < kG; j++) greedyAisles.add(aisleOrderByScore[j]);

                                        // capacidades por ítem
                                        int[] cap = new int[N];
                                        for (int a : greedyAisles) {
                                            for (Map.Entry<Integer,Integer> e : aisles.get(a).entrySet()) {
                                                int i = e.getKey(), s = e.getValue();
                                                if (i >= 0 && i < N && s > 0) cap[i] += s;
                                            }
                                        }

                                        // ordenar órdenes: u desc, luego τ desc
                                        Integer[] ordOrder = new Integer[numOrders];
                                        for (int o = 0; o < numOrders; o++) ordOrder[o] = o;
                                        Arrays.sort(ordOrder, (o1, o2) -> {
                                            int c = Integer.compare(unitsPerOrder[o2], unitsPerOrder[o1]);
                                            if (c != 0) return c;
                                            return Integer.compare(typesPerOrder[o2], typesPerOrder[o1]);
                                        });

                                        // selección de órdenes cumpliendo stock y [LB,UB] (y tipos si aplica)
                                        Set<Integer> greedyOrders = new HashSet<>();
                                        long unitsSum = 0L;
                                        long tauSum   = 0L;

                                        java.util.function.IntPredicate fits = (o) -> {
                                            for (Map.Entry<Integer,Integer> e : orders.get(o).entrySet()) {
                                                int i = e.getKey(), d = e.getValue();
                                                if (d <= 0) continue;
                                                if (i < 0 || i >= N) return false;
                                                if (cap[i] < d) return false;
                                            }
                                            return true;
                                        };

                                        for (int oo = 0; oo < numOrders; oo++) {
                                            int o = ordOrder[oo];
                                            int uo = unitsPerOrder[o];
                                            if (uo <= 0) continue;
                                            if (unitsSum + uo > (long) ub) continue;
                                            if (haveTypeBoundsG && (tauSum + typesPerOrder[o] > ubTypesG)) continue;
                                            if (!fits.test(o)) continue;

                                            greedyOrders.add(o);
                                            unitsSum += uo;
                                            tauSum   += typesPerOrder[o];
                                            for (Map.Entry<Integer,Integer> e : orders.get(o).entrySet()) {
                                                int i = e.getKey(), d = e.getValue();
                                                if (d > 0 && 0 <= i && i < N) cap[i] -= d;
                                            }
                                            if (unitsSum >= (long) lb) break;
                                        }

                                        if (unitsSum < (long) lb) {
                                            Arrays.sort(ordOrder, Comparator.comparingInt(o -> unitsPerOrder[(int) o]));
                                            for (int oo = 0; oo < numOrders && unitsSum < (long) lb; oo++) {
                                                int o = ordOrder[oo];
                                                if (greedyOrders.contains(o)) continue;
                                                int uo = unitsPerOrder[o];
                                                if (uo <= 0 || unitsSum + uo > (long) ub) continue;
                                                if (haveTypeBoundsG && (tauSum + typesPerOrder[o] > ubTypesG)) continue;
                                                if (!fits.test(o)) continue;

                                                greedyOrders.add(o);
                                                unitsSum += uo;
                                                tauSum   += typesPerOrder[o];
                                                for (Map.Entry<Integer,Integer> e : orders.get(o).entrySet()) {
                                                    int i = e.getKey(), d = e.getValue();
                                                    if (d > 0 && 0 <= i && i < N) cap[i] -= d;
                                                }
                                            }
                                        }

                                        final long g1 = System.nanoTime();
                                        System.out.printf(Locale.US,
                                                "[Greedy] Construcción en %.3f ms | k=%d pasillos | U=%,d (LB=%d, UB=%d) | tipos=%s%n",
                                                (g1 - g0) / 1e6, kG, unitsSum, lb, ub,
                                                (haveTypeBoundsG ? (tauSum + " in [" + lbTypesG + "," + ubTypesG + "]") : "N/A")
                                        );

                                        boolean feasibleGreedy = (greedyAisles.size() == kG) &&
                                                (unitsSum >= (long) lb) &&
                                                (unitsSum <= (long) ub) &&
                                                (!haveTypeBoundsG || (tauSum >= lbTypesG && tauSum <= ubTypesG));

                                        if (feasibleGreedy) {
                                            List<IloNumVar> startVars = new ArrayList<>(greedyOrders.size() + greedyAisles.size());
                                            List<Double>    startVals = new ArrayList<>(greedyOrders.size() + greedyAisles.size());
                                            for (int o : greedyOrders) { startVars.add(xVar[o]); startVals.add(1.0); }
                                            for (int a : greedyAisles) { startVars.add(yVar[a]); startVals.add(1.0); }
                                            try {
                                                cpx.addMIPStart(startVars.toArray(new IloNumVar[0]),
                                                        startVals.stream().mapToDouble(d -> d).toArray());
                                                System.out.printf(Locale.US,
                                                        "[Greedy] MIP start aplicado: |O|=%d, |A|=%d%n",
                                                        greedyOrders.size(), greedyAisles.size()
                                                );
                                            } catch (Exception __) {
                                                System.out.println("[Greedy] No se pudo aplicar MIP start (continuo sin él).");
                                            }
                                        } else {
                                            System.out.println("[Greedy] No se logró una solución inicial factible con k pasillos (se continúa sin MIP start).");
                                        }
                                    }
                                }
                                // ===== Fin Greedy =====

                                // Callback tipo "cortar_por_bound" (dos cortes: tiempo sin incumbente y bound dominado)
                                final long tStartMs = System.currentTimeMillis();
                                final double mejorHastaAhora = currentObj; // snapshot del mejor global al arrancar esta k

                                cpx.use(new IloCplex.MIPInfoCallback() {
                                    private Double ultimoGap = null;
                                    private double tUltimoCrec = 0.0;

                                    @Override protected void main() throws IloException {
                                        final double t = (System.currentTimeMillis() - tStartMs) / 1000.0;

                                        if (hasIncumbent()) {
                                            hayIncumbente.set(true); // avisa al Watchdog que ya hay solución
                                        }

                                        // CORTE POR BOUND DOMINADO:
                                        // maximizamos; getBestObjValue() es cota superior. Si bound ≤ mejor actual, no hay mejora posible.
                                        try {
                                            double bound = getBestObjValue();
                                            if (!Double.isNaN(bound) && !Double.isInfinite(bound)) {
                                                if (bound <= mejorHastaAhora + 1e-9) {
                                                    System.out.printf(Locale.US,
                                                        "[Callback] Bound %.6f ≤ mejor actual %.6f → abort()%n",
                                                        bound, mejorHastaAhora);
                                                    abort();
                                                    return;
                                                }
                                            }
                                        } catch (Throwable __) { /* bound aún no disponible, seguimos */ }

                                        // (Opcional) estancamiento de GAP (solo si ya hay incumbente)
                                        if (hasIncumbent()) {
                                            double bound = getBestObjValue();
                                            double incumbent = getIncumbentObjValue();
                                            if (Math.abs(bound) > 1e-12) {
                                                double gap = (bound - incumbent) / Math.abs(bound);
                                                if (ultimoGap == null || Math.abs(gap - ultimoGap) > 1e-12) {
                                                    tUltimoCrec = t;
                                                    if (((int) Math.round(t)) % 5 == 0) {
                                                        System.out.printf(Locale.US, "[Callback@MIP] GAP=%.4f%n", gap);
                                                    }
                                                } else {
                                                    double tiempo_estancado = t - tUltimoCrec;
                                                    if (tiempo_estancado >= 22.0 && t >= 40.0) {
                                                        System.out.printf(Locale.US, "[Callback@MIP] Aborto por estancamiento (%.2fs).%n", tiempo_estancado);
                                                        abort();
                                                        return;
                                                    }
                                                }
                                                ultimoGap = gap;
                                            }
                                        }

                                        // Redundante con el Watchdog pero útil si ya estamos ramificando:
                                        if (!hasIncumbent() && t > noIncCutoff) {
                                            System.out.printf(Locale.US, "[Callback] Sin incumbente en %.2fs → abort()%n", t);
                                            abort();
                                        }
                                    }
                                });


                                // Optimizar
                                double t0 = System.nanoTime() / 1e9;
                                boolean ok = cpx.solve();
                                double t1 = System.nanoTime() / 1e9;
                                // Apaga el watchdog sí o sí para que no quede vivo
                                watchdog.cancel();

                                // Imprime motivo de término
                                try {
                                    IloCplex.CplexStatus why = cpx.getCplexStatus();
                                    if (why == IloCplex.CplexStatus.AbortUser) {
                                        System.out.println("Corte anticipado por usuario (watchdog/callback).");
                                    } else if (why == IloCplex.CplexStatus.AbortTimeLim) {
                                        System.out.println("No se encontró una solución en el tiempo límite.");
                                    } else {
                                        System.out.println("Status CPLEX: " + why);
                                    }
                                } catch (Exception __) { /* ignore */ }

                                System.out.printf(Locale.US, "Tiempo real: %.2f segundos | pasillos intentados: %d%n", (t1 - t0), num_pasillos);

                                Double boundVal = null;
                                if (ok && cpx.getStatus() == IloCplex.Status.Optimal) {
                                    System.out.printf(Locale.US, "Se alcanzó la solución óptima para la cantidad de pasillos fijada en %d%n", num_pasillos);
                                    double objVal = cpx.getObjValue(); // = (unidades)/num_pasillos
                                    if (objVal > 0.0) {
                                        pasillos_objetivos.add((int) Math.floor(ub / objVal));
                                    }
                                } else {
                                    try {
                                        boundVal = cpx.getBestObjValue();
                                        System.out.printf(Locale.US, "El mayor valor de los nodos (bound) es: %.6f%n", boundVal);
                                        if (boundVal <= currentObj + 1e-9) {
                                            System.out.printf(Locale.US,
                                                "[PostSolve] Bound %.6f ≤ mejor actual %.6f → no hay mejora posible con k=%d%n",
                                                boundVal, currentObj, num_pasillos);
                                        }

                                    } catch (Exception __) {
                                        System.out.println("No se pudo recuperar el bound del modelo.");
                                    }
                                }

                                // ¿Hay solución?
                            if (!ok || (cpx.getStatus() == IloCplex.Status.Infeasible)) {
                                if (cpx.getStatus() == IloCplex.Status.Infeasible) {
                                    System.out.println("Modelo infactible.");
                                    pasillos_infactibles.add(num_pasillos);  // Guardar como infactible
                                } else if (cpx.getCplexStatus() == IloCplex.CplexStatus.AbortTimeLim) {
                                    System.out.println("No se encontró una solución en el tiempo límite.");
                                } else {
                                    System.out.println("Modelo sin solución encontrada.");
                                }
                                System.out.println("fin -------------------------------------------------------------------------------------------------------------------");
                                // candidate permanece como current

                                } else {
                                    // Extraer solución
                                    Set<Integer> SO = new HashSet<>();
                                    Set<Integer> SA = new HashSet<>();
                                    for (int o = 0; o < numOrders; o++) if (cpx.getValue(xVar[o]) > 1e-6) SO.add(o);
                                    for (int a = 0; a < numAisles; a++) if (cpx.getValue(yVar[a]) > 1e-6) SA.add(a);

                                    ChallengeSolution nueva = new ChallengeSolution(SO, SA);

                                    double newObj = evalObj.applyAsDouble(nueva);
                                    if (newObj > currentObj) {
                                        if (boundVal != null) {
                                            double mejora = (boundVal - newObj) / boundVal * 100.0;
                                            System.out.printf(Locale.US,
                                                    "Nueva mejor solución %.4f con %d pasillos, con un posible porcentaje de mejora de %.2f%%%n",
                                                    newObj, num_pasillos, mejora);
                                        } else {
                                            System.out.printf(Locale.US,
                                                    "Nueva mejor solución %.4f con %d pasillos (bound no disponible)%n",
                                                    newObj, num_pasillos);
                                        }
                                        candidate = nueva;
                                    }
                                    System.out.printf(Locale.US, "TIEMPO RESTANTE: %.2f seg.%n", Math.max(0.0, tiempo_restante - (t1 - t0)));
                                    System.out.println("fin -------------------------------------------------------------------------------------------------------------------");
                                }
                            } catch (IloException e) {
                                e.printStackTrace();
                                System.out.println("fin -------------------------------------------------------------------------------------------------------------------");
                                // candidate permanece como current
                            }
                        }
                    }

            
                } 
                else {
                // ------------------- h2: Dinkelbach (una iteración) -------------------
                System.out.println("inicio Dinkelbach -----------------------------------------------------------------------------------------------");

                // Tiempo desde MAX_RUNTIME (ms -> s)
                final double restTime = Math.max(1.0, (double) getRemainingTime(stopWatch));
                final int tiempoCorrer = 25 + new Random().nextInt(21); // [25,45] como tope blando
                final int numIt = (int) Math.max(1, Math.min(Math.floor(restTime - 1.0), tiempoCorrer));


                // q = obj de la solución anterior (unidades/pasillos)
                Set<Integer> prevSelOrders = (current != null ? current.orders() : Collections.emptySet());
                Set<Integer> prevSelAisles = (current != null ? current.aisles() : Collections.emptySet());
                double unitsPrev = 0.0;
                if (prevSelOrders != null) {
                    for (int o : prevSelOrders) for (int v : orders.get(o).values()) unitsPrev += v;
                }
                int pasPrev = (prevSelAisles == null) ? 0 : prevSelAisles.size();
                final double prevObj = (pasPrev == 0) ? 0.0 : (unitsPrev / pasPrev);
                final double qKey = Math.round(prevObj * 1e6) / 1e6; // redondea para comparar

                if (Q_USADOS_GLOBAL.contains(qKey)) {
                    System.out.printf(Locale.US, "q = %.2f ya fue usado.%n", prevObj);
                    System.out.println("fin Dinkelbach -----------------------------------------------------------------------------------------------");
                } else {
                    Q_USADOS_GLOBAL.add(qKey);
                    System.out.printf(Locale.US, "q actual: %.2f | q usados: %s | tiempo de ejecución: %d seg.%n",
                            prevObj, Q_USADOS_GLOBAL.toString(), tiempoCorrer);

                    if (numOrders == 0 || numAisles == 0) {
                        System.out.println("No hay órdenes o pasillos; omito Dinkelbach.");
                        System.out.println("fin Dinkelbach -----------------------------------------------------------------------------------------------");
                    } else {
                        // ===== Preagregado esparso por ítem =====
                        @SuppressWarnings("unchecked") ArrayList<int[]>[] demandPairs = new ArrayList[N];
                        @SuppressWarnings("unchecked") ArrayList<int[]>[] supplyPairs = new ArrayList[N];

                        for (int o = 0; o < numOrders; o++) {
                            for (Map.Entry<Integer, Integer> e : orders.get(o).entrySet()) {
                                int i = e.getKey(), qty = e.getValue();
                                if (qty == 0 || i < 0) continue; if (i >= N) continue;
                                ArrayList<int[]> list = demandPairs[i];
                                if (list == null) { list = new ArrayList<>(); demandPairs[i] = list; }
                                list.add(new int[]{o, qty});
                            }
                        }
                        for (int a = 0; a < numAisles; a++) {
                            for (Map.Entry<Integer, Integer> e : aisles.get(a).entrySet()) {
                                int i = e.getKey(), stk = e.getValue();
                                if (stk == 0 || i < 0) continue; if (i >= N) continue;
                                ArrayList<int[]> list = supplyPairs[i];
                                if (list == null) { list = new ArrayList<>(); supplyPairs[i] = list; }
                                list.add(new int[]{a, stk});
                            }
                        }

                        IloCplex cpx = null;
                        try {
                            cpx = new IloCplex();
                            cpx.setParam(IloCplex.Param.MIP.Display, 0);
                            cpx.setParam(IloCplex.Param.TimeLimit, (double) numIt);
                            try { cpx.setParam(IloCplex.Param.Threads, 1); } catch (Throwable __) {}

                            // Variables
                            IloNumVar[] xVar = cpx.boolVarArray(numOrders);
                            IloNumVar[] yVar = cpx.boolVarArray(numAisles);

                            // Stock por ítem
                            for (int i = 0; i < N; i++) {
                                ArrayList<int[]> dem = demandPairs[i];
                                if (dem == null || dem.isEmpty()) continue;
                                IloLinearNumExpr lhs = cpx.linearNumExpr();
                                for (int[] p : dem) lhs.addTerm(p[1], xVar[p[0]]);

                                ArrayList<int[]> sup = supplyPairs[i];
                                if (sup == null || sup.isEmpty()) {
                                    cpx.addLe(lhs, 0.0);
                                } else {
                                    IloLinearNumExpr rhs = cpx.linearNumExpr();
                                    for (int[] p : sup) rhs.addTerm(p[1], yVar[p[0]]);
                                    cpx.addLe(lhs, rhs);
                                }
                            }

                            // Cotas de unidades
                            IloLinearNumExpr totalUnits = cpx.linearNumExpr();
                            for (int o = 0; o < numOrders; o++) {
                                int uo = unitsPerOrder[o];
                                if (uo != 0) totalUnits.addTerm(uo, xVar[o]);
                            }
                            cpx.addLe(totalUnits, waveSizeUB);
                            cpx.addGe(totalUnits, waveSizeLB);

                            // Objetivo Dinkelbach: max totalUnits - q * sum(y)
                            IloLinearNumExpr sumY = cpx.linearNumExpr();
                            for (int a = 0; a < numAisles; a++) sumY.addTerm(1.0, yVar[a]);
                            IloNumExpr obj = cpx.diff(totalUnits, cpx.prod(prevObj, sumY));
                            cpx.addMaximize(obj);

                            // Fijaciones rápidas (≤2 s), protegidas contra listas vacías
                            boolean aplicarFijaciones = true;
                            final long tFix0 = System.nanoTime();

                            List<int[]> enSol = new ArrayList<>();
                            if (prevSelOrders != null) {
                                for (int o : prevSelOrders) enSol.add(new int[]{o, unitsPerOrder[o]});
                            }
                            enSol.sort((a,b) -> Integer.compare(b[1], a[1])); // desc

                            Set<Integer> setPrev = (prevSelOrders == null) ? Collections.emptySet() : prevSelOrders;
                            List<int[]> fueraSol = new ArrayList<>();
                            for (int o = 0; o < numOrders; o++) if (!setPrev.contains(o)) fueraSol.add(new int[]{o, unitsPerOrder[o]});
                            fueraSol.sort(Comparator.comparingInt(a -> a[1])); // asc

                            if ((System.nanoTime() - tFix0) / 1e9 > 2.0) aplicarFijaciones = false;

                            if (aplicarFijaciones && !enSol.isEmpty()) {
                                int topLen = enSol.size() / 2; // puede ser 0
                                if (topLen > 0) {
                                    List<Integer> topIdx = new ArrayList<>(topLen);
                                    for (int i = 0; i < topLen; i++) topIdx.add(enSol.get(i)[0]);
                                    int k1 = (int) Math.floor(0.1 * topIdx.size());
                                    if (k1 > 0) {
                                        Collections.shuffle(topIdx);
                                        for (int i = 0; i < Math.min(k1, topIdx.size()); i++) cpx.addEq(xVar[topIdx.get(i)], 1.0);
                                    }
                                }
                            } else if (aplicarFijaciones) {
                                System.out.println("No hay órdenes previas; omito fijaciones positivas.");
                            }

                            if (aplicarFijaciones && !fueraSol.isEmpty()) {
                                int botLen = fueraSol.size() / 2; // puede ser 0
                                if (botLen > 0) {
                                    List<Integer> botIdx = new ArrayList<>(botLen);
                                    for (int i = 0; i < botLen; i++) botIdx.add(fueraSol.get(i)[0]);
                                    int k0 = (int) Math.floor(0.1 * botIdx.size());
                                    if (k0 > 0) {
                                        Collections.shuffle(botIdx);
                                        for (int i = 0; i < Math.min(k0, botIdx.size()); i++) cpx.addEq(xVar[botIdx.get(i)], 0.0);
                                    }
                                }
                            } else if (aplicarFijaciones) {
                                System.out.println("No hay órdenes fuera de la solución; omito fijaciones negativas.");
                            }

                            if (!aplicarFijaciones) System.out.println("Fijaciones omitidas por exceder el límite de 2 segundos.");

                            // MIP start
                            if (prevSelOrders != null && prevSelAisles != null && !prevSelOrders.isEmpty()) {
                                List<IloNumVar> startVars = new ArrayList<>();
                                List<Double> startVals = new ArrayList<>();
                                for (int o : prevSelOrders) { startVars.add(xVar[o]); startVals.add(1.0); }
                                for (int a : prevSelAisles) { startVars.add(yVar[a]); startVals.add(1.0); }
                                try {
                                    cpx.addMIPStart(startVars.toArray(new IloNumVar[0]),
                                            startVals.stream().mapToDouble(d -> d).toArray());
                                } catch (Exception __) {}
                            }

                            // Solve + prints
                            double t0 = System.nanoTime() / 1e9;
                            boolean ok = cpx.solve();
                            double t1 = System.nanoTime() / 1e9;
                            System.out.println("La resolución tuvo una duración de " + (t1 - t0) + " segundos");

                            if (ok && cpx.getStatus() == IloCplex.Status.Optimal) {
                                System.out.printf(Locale.US, "Se alcanzó la solución óptima para q = %.2f se guardará en usados.%n", prevObj);
                            } else {
                                try {
                                    double bound = cpx.getBestObjValue();
                                    double pct = (prevObj != 0.0) ? Math.abs((bound - prevObj) / prevObj * 100.0) : 0.0;
                                    System.out.printf(Locale.US,
                                            "El mayor valor de los nodos es: %.2f y hay un porcentaje de %.2f%% con respecto a la solución anterior.%n",
                                            bound, pct);
                                } catch (Exception __) {
                                    System.out.println("No se pudo recuperar el bound del modelo.");
                                }
                            }

                            // Extraer solución y armar 'candidate'
                            if (ok) {
                                Set<Integer> SO = new HashSet<>();
                                Set<Integer> SA = new HashSet<>();
                                for (int o = 0; o < numOrders; o++) if (cpx.getValue(xVar[o]) > 0.5) SO.add(o);
                                for (int a = 0; a < numAisles; a++) if (cpx.getValue(yVar[a]) > 0.5) SA.add(a);

                                double picked = 0.0;
                                for (int o : SO) for (int v : orders.get(o).values()) picked += v;
                                int pas = SA.size();
                                double objReal = (pas == 0) ? 0.0 : (picked / pas);

                                candidate = new ChallengeSolution(SO, SA);
                                System.out.printf(Locale.US, "nueva solución: %.2f%n", objReal);
                            }

                            double restAfter = Math.max(0.0, restTime - (t1 - t0));
                            System.out.printf(Locale.US, "TIEMPO RESTANTE: %.2f seg.%n", restAfter);
                            System.out.println("fin Dinkelbach -----------------------------------------------------------------------------------------------");
                        } catch (Exception ex) { // captura IndexOutOfBounds y otros
                            ex.printStackTrace();
                            System.out.println("fin Dinkelbach -----------------------------------------------------------------------------------------------");
                        } finally {
                            try { if (cpx != null) cpx.end(); } catch (Throwable __) {}
                        }
                    }
                }
                //---------------------- Termino H2
            }
            
            // ... justo después de terminar H1/H2:
            long th1 = System.nanoTime();

            // NUEVO: tiempo global al “llegar” a la solución candidata y tiempo restante
            double tSolSec = (stopWatch != null) ? stopWatch.getTime(TimeUnit.MILLISECONDS) / 1000.0 : Double.NaN;
            double tRemSec = (stopWatch != null) ? getRemainingTime(stopWatch) : Double.NaN;

            // Evaluar candidato y best-actual antes de actualizar el bandit
            int candA = (candidate.aisles() == null) ? 0 : candidate.aisles().size();
            int candU = 0;
            if (candidate.orders() != null) {
                for (int o : candidate.orders()) for (int v : orders.get(o).values()) candU += v;
            }
            double candObj = (candA == 0 ? 0.0 : ((double) candU) / candA);

            // Best actual (= current) ANTES de aceptar o no al candidato
            int bestA = (current.aisles() == null) ? 0 : current.aisles().size();
            int bestU = 0;
            if (current.orders() != null) {
                for (int o : current.orders()) for (int v : orders.get(o).values()) bestU += v;
            }
            double bestObj = (bestA == 0 ? 0.0 : ((double) bestU) / bestA);

            // Print comparando candidato vs best
            System.out.printf(
                Locale.US,
                "[Iter %d @ t=%.2fs | rem=%.2fs] %s => cand=%.4f [U=%d,A=%d] | best=%.4f [U=%d,A=%d] | p1=%.3f,p2=%.3f | Δt=%.2f s%n",
                t, tSolSec, tRemSec, who,
                candObj, candU, candA,
                bestObj, bestU, bestA,
                p1, p2,
                (th1 - th0) / 1e9
            );


            if (candObj > currentObj) {
                current = candidate;
                currentObj = candObj;
                // marca de tiempo de la última mejor solución
                tBestSec = (stopWatch != null) ? stopWatch.getTime(TimeUnit.MILLISECONDS) / 1000.0 : -1.0;
                bestObjEver = currentObj;

                if (useH1) T1++; else T2++;
                p1 = (double) T1 / (T1 + T2);
                p2 = 1.0 - p1;
                System.out.printf(Locale.US, "   Mejora -> T1=%d, T2=%d | p1=%.3f, p2=%.3f%n", T1, T2, p1, p2);
            } else {
                System.out.println("   No mejora: probabilidades se mantienen.");
            }

        }

        // ===== Resultado final =====
        int finA = (current.aisles() == null) ? 0 : current.aisles().size();
        int finU = 0; if (current.orders() != null) for (int o : current.orders()) for (int v : orders.get(o).values()) finU += v;
        System.out.printf(Locale.US, "[Final] obj=%.4f | U=%d | A=%d%n",
        (finA == 0 ? 0.0 : ((double) finU) / finA), finU, finA);

        // Resumen: ¿cuándo se alcanzó la ÚLTIMA mejor solución dentro de los 10 minutos?
        System.out.printf(Locale.US,
                "[Mejor alcanzada] obj=%.4f | t=%.2f s desde el inicio | faltaba=%.2f s%n",
                bestObjEver,
                tBestSec,
                (tBestSec >= 0.0 ? Math.max(0.0, (MAX_RUNTIME / 1000.0) - tBestSec) : -1.0)
);

return current;

    }

    // ===== Helpers =====
    /** Devuelve un N robusto (= max(nItems, maxIndex+1)) para evitar out-of-bounds si hay claves fuera de rango. */
    // === Helpers para fallback de Dinkelbach desde H1 ===
    private static double round6(double v) { return Math.round(v * 1e6) / 1e6; }

    private ChallengeSolution runDinkelbachWithQ(double q,
                                                double tlSeconds,
                                                int[] unitsPerOrder,
                                                int N) {
        if (q <= 0.0 || tlSeconds <= 0.0) return null;
        try (IloCplex cpx = new IloCplex()) {
            cpx.setOut(null);        // apaga
            cpx.setWarning(null);    // apaga warnings de CPLEX
            cpx.setParam(IloCplex.Param.MIP.Display, 0);
            cpx.setParam(IloCplex.Param.TimeLimit, tlSeconds);
            try { cpx.setParam(IloCplex.Param.Threads, 1); } catch (Throwable __) {}

            final int numOrders = orders.size();
            final int numAisles = aisles.size();

            IloNumVar[] xVar = cpx.boolVarArray(numOrders);
            IloNumVar[] yVar = cpx.boolVarArray(numAisles);

            // Stock por ítem
            for (int i = 0; i < N; i++) {
                // LHS: demanda
                IloLinearNumExpr lhs = cpx.linearNumExpr();
                boolean hasDem = false;
                for (int o = 0; o < numOrders; o++) {
                    Integer dem = orders.get(o).get(i);
                    if (dem != null && dem > 0) {
                        lhs.addTerm(dem, xVar[o]);
                        hasDem = true;
                    }
                }
                if (!hasDem) continue; // si no hay demanda para el ítem i, no agregamos restricción

                // RHS: oferta
                IloLinearNumExpr rhs = cpx.linearNumExpr();
                boolean hasSup = false;
                for (int a = 0; a < numAisles; a++) {
                    Integer sup = aisles.get(a).get(i);
                    if (sup != null && sup > 0) {
                        rhs.addTerm(sup, yVar[a]);
                        hasSup = true;
                    }
                }

                if (!hasSup) {
                    // No hay oferta del ítem i en ningún pasillo: exigir 0 en la demanda
                    cpx.addLe(lhs, 0.0);
                } else {
                    cpx.addLe(lhs, rhs);
                }
            }


            // Cotas LB/UB unidades
            IloLinearNumExpr totalUnits = cpx.linearNumExpr();
            for (int o = 0; o < numOrders; o++) {
                int uo = unitsPerOrder[o];
                if (uo != 0) totalUnits.addTerm(uo, xVar[o]);
            }
            cpx.addGe(totalUnits, waveSizeLB);
            cpx.addLe(totalUnits, waveSizeUB);

            // Objetivo: totalUnits - q * sum(y)
            IloLinearNumExpr sumY = cpx.linearNumExpr();
            for (int a = 0; a < numAisles; a++) sumY.addTerm(1.0, yVar[a]);
            cpx.addMaximize(cpx.diff(totalUnits, cpx.prod(q, sumY)));

            boolean ok = cpx.solve();
            if (!ok) return null;

            Set<Integer> SO = new HashSet<>();
            Set<Integer> SA = new HashSet<>();
            for (int o = 0; o < numOrders; o++) if (cpx.getValue(xVar[o]) > 0.5) SO.add(o);
            for (int a = 0; a < numAisles; a++) if (cpx.getValue(yVar[a]) > 0.5) SA.add(a);

            return new ChallengeSolution(SO, SA);
        } catch (IloException __) {
            return null;
        }
    }

    private int effectiveNItems() {
        int maxIdx = -1;
        for (Map<Integer, Integer> m : orders) for (Integer k : m.keySet()) if (k != null && k > maxIdx) maxIdx = k;
        for (Map<Integer, Integer> m : aisles) for (Integer k : m.keySet()) if (k != null && k > maxIdx) maxIdx = k;
        return Math.max(nItems, maxIdx + 1);
    }


    /*
     * Get the remaining time in seconds
     */
    protected long getRemainingTime(StopWatch stopWatch) {
        return Math.max(
                TimeUnit.SECONDS.convert(MAX_RUNTIME - stopWatch.getTime(TimeUnit.MILLISECONDS), TimeUnit.MILLISECONDS),
                0);
    }

    protected boolean isSolutionFeasible(ChallengeSolution challengeSolution) {
        Set<Integer> selectedOrders = challengeSolution.orders();
        Set<Integer> visitedAisles = challengeSolution.aisles();
        if (selectedOrders == null || visitedAisles == null || selectedOrders.isEmpty() || visitedAisles.isEmpty()) {
            return false;
        }

        int[] totalUnitsPicked = new int[nItems];
        int[] totalUnitsAvailable = new int[nItems];

        // Calculate total units picked
        for (int order : selectedOrders) {
            for (Map.Entry<Integer, Integer> entry : orders.get(order).entrySet()) {
                totalUnitsPicked[entry.getKey()] += entry.getValue();
            }
        }

        // Calculate total units available
        for (int aisle : visitedAisles) {
            for (Map.Entry<Integer, Integer> entry : aisles.get(aisle).entrySet()) {
                totalUnitsAvailable[entry.getKey()] += entry.getValue();
            }
        }

        // Check if the total units picked are within bounds
        int totalUnits = Arrays.stream(totalUnitsPicked).sum();
        if (totalUnits < waveSizeLB || totalUnits > waveSizeUB) {
            return false;
        }

        // Check if the units picked do not exceed the units available
        for (int i = 0; i < nItems; i++) {
            if (totalUnitsPicked[i] > totalUnitsAvailable[i]) {
                return false;
            }
        }

        return true;
    }

    protected double computeObjectiveFunction(ChallengeSolution challengeSolution) {
        Set<Integer> selectedOrders = challengeSolution.orders();
        Set<Integer> visitedAisles = challengeSolution.aisles();
        if (selectedOrders == null || visitedAisles == null || selectedOrders.isEmpty() || visitedAisles.isEmpty()) {
            return 0.0;
        }
        int totalUnitsPicked = 0;

        // Calculate total units picked
        for (int order : selectedOrders) {
            totalUnitsPicked += orders.get(order).values().stream()
                    .mapToInt(Integer::intValue)
                    .sum();
        }

        // Calculate the number of visited aisles
        int numVisitedAisles = visitedAisles.size();

        // Objective function: total units picked / number of visited aisles
        return (double) totalUnitsPicked / numVisitedAisles;
    }
}