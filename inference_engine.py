"""
Motor de Inferencia — Encadenamiento hacia Adelante (Forward Chaining).

Recibe el diccionario de hechos producido por fuzzy_engine.construir_hechos()
y evalúa las reglas de knowledge_base.REGLAS en orden de prioridad clínica,
registrando cada regla disparada y resolviendo conflictos por jerarquía de decisión.

Jerarquía de arbitraje (de mayor a menor precedencia):
    4 — Cuarentena / Rechazo Técnico  (R20)
    3 — Descarte + Diferido Permanente (infección confirmada, sin reingreso)
    2 — Descarte + Diferido Temporal   (infección tratable o duda inicial)
    1 — Descarte sin estado de donante explícito
    0 — Apta / Habilitado
"""

from knowledge_base import REGLAS

# ---------------------------------------------------------------------------
# Funciones auxiliares
# ---------------------------------------------------------------------------

def _peso_decision(decision):
    """Devuelve el peso jerárquico de un diccionario de decisión para arbitraje."""
    unidad  = (decision.get("unidad") or "").lower().strip()
    donante = (decision.get("donante") or "").lower().strip()
    if unidad == "cuarentena":
        return 4
    if unidad == "descarte" and donante == "diferido permanente":
        return 3
    if unidad == "descarte" and donante == "diferido temporal":
        return 2
    if unidad == "descarte":
        return 1
    return 0  # Apta u otras


def _decision_de_regla(regla, hechos):
    """Construye el diccionario de decisión a partir de una regla disparada."""
    return {
        "unidad":   regla.get("unidad"),
        "donante":  regla.get("donante"),
        "resultado": regla.get("resultado"),
        "accion":   regla.get("accion"),
        "certeza":  hechos.get("certeza_sco", 100.0),
    }


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def match_condiciones(condiciones, hechos):
    """
    Verifica si todas las condiciones de una regla coinciden con los hechos.
    Lógica AND implícita: todas las claves deben satisfacerse.
    Soporta igualdad exacta, comparación con listas (semántica OR)
    y predicados callable (para rangos numéricos u otras condiciones complejas).
    """
    for clave, valor_esperado in condiciones.items():
        valor_actual = hechos.get(clave)
        if callable(valor_esperado):
            if not valor_esperado(valor_actual):
                return False
        elif isinstance(valor_esperado, (list, tuple)):
            if valor_actual not in valor_esperado:
                return False
        else:
            if valor_actual != valor_esperado:
                return False
    return True


def evaluar_reglas(hechos):
    """
    Aplica Forward Chaining sobre la Base de Conocimientos.

    Proceso:
        1. Ordena las reglas dinámicamente por el campo "prioridad" (mayor primero).
        2. Dispara cada regla cuyas condiciones coincidan con hechos.
        3. R20 produce un corte inmediato (rechazo técnico).
        4. Las reglas de acción intermedia (sin campo "unidad") se registran
           pero no bloquean la búsqueda de decisión final.
        5. Al finalizar, arbitra conflictos por jerarquía y aplica fallback a Apta.

    Retorna: (decision_final: dict, reglas_activadas: list[dict])
    """
    reglas_ordenadas = sorted(REGLAS, key=lambda r: r.get("prioridad", 0), reverse=True)
    reglas_activadas = []
    decision_final = None

    for regla in reglas_ordenadas:
        regla_id = regla["id"]

        if not match_condiciones(regla["condiciones"], hechos):
            continue

        reglas_activadas.append(regla)

        # R20: corte inmediato — ninguna otra regla se evalúa
        if regla_id == "R20":
            decision_final = {
                "unidad":    regla.get("unidad", "Cuarentena"),
                "donante":   None,
                "resultado": regla.get("resultado", "Rechazo Técnico"),
                "accion":    None,
                "certeza":   100.0,
            }
            return decision_final, reglas_activadas

        # Reglas de acción intermedia (sin "unidad"): se registran pero no bloquean
        if regla.get("unidad") is None:
            continue

        # Arbitrar por jerarquía de decisión
        candidata = _decision_de_regla(regla, hechos)
        if decision_final is None or _peso_decision(candidata) > _peso_decision(decision_final):
            decision_final = candidata

    # ---------------------------------------------------------------------------
    # Post-iteración: fallbacks
    # ---------------------------------------------------------------------------

    # Si solo dispararon reglas de acción (ej. R2_* sin datos de repetición)
    if decision_final is None:
        for regla in reglas_activadas:
            if regla.get("unidad") is None:
                decision_final = {
                    "unidad":    None,
                    "donante":   None,
                    "resultado": "Pendiente",
                    "accion":    regla.get("accion"),
                    "certeza":   hechos.get("certeza_sco", 100.0),
                }
                break

    # Fallback a Apta implícita: sin alertas, sin riesgo, S/CO negativo
    # (cubre marcadores sin NAT como Chagas/Brucelosis cuando todo es negativo)
    if decision_final is None:
        sco_negativo  = hechos.get("sco") == "No Reactivo"
        sin_riesgo    = hechos.get("riesgo") == "No"
        nat_ok        = hechos.get("nat") != "Reactivo"
        vdrl_ok       = hechos.get("vdrl") != "Reactivo"
        sin_zona_gris = hechos.get("sco_inicial") != "Zona Gris"

        if sco_negativo and sin_riesgo and nat_ok and vdrl_ok and sin_zona_gris:
            decision_final = {
                "unidad":    "Apta",
                "donante":   "Habilitado",
                "resultado": None,
                "accion":    None,
                "certeza":   hechos.get("certeza_sco", 100.0),
            }

    return decision_final, reglas_activadas
