"""
Orquestador Central del Sistema Experto de Seguridad Transfusional.

Coordina el flujo completo:
    1. Pre-procesamiento difuso  (fuzzy_engine.construir_hechos)
    2. Inferencia con Forward Chaining  (inference_engine.evaluar_reglas)
    3. Generación del Subsistema de Explicación

API pública: evaluar_caso(datos) → dict
"""

from fuzzy_engine import construir_hechos
from inference_engine import evaluar_reglas


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------

def evaluar_caso(datos):
    """
    Punto de entrada del sistema experto.

    Parámetros (dict 'datos') — ver fuzzy_engine.construir_hechos() para detalle.

    Retorna dict con:
        unidad           (str|None)  : "Apta" | "Descarte" | "Cuarentena"
        donante          (str|None)  : "Habilitado" | "Diferido Temporal" | "Diferido Permanente"
        resultado        (str|None)  : "Rechazo Técnico" | "Pendiente" | None
        accion           (str|None)  : Acción intermedia requerida (ej. repetir, pedir CLIA)
        certeza          (float)     : Nivel de certeza difusa de la clasificación S/CO [0-100]
        sco_etiqueta     (str|None)  : Clasificación lingüística del S/CO inicial
        reglas_activadas (list[str]) : IDs de reglas disparadas, en orden
        explicacion      (str)       : Texto del Subsistema de Explicación
    """
    # Fase 1 — Pre-procesamiento difuso: datos crudos → hechos normalizados
    hechos = construir_hechos(datos)

    # Fase 2 — Inferencia: hechos → decisión + trazabilidad
    decision, reglas_activadas = evaluar_reglas(hechos)

    if decision is None:
        decision = {
            "unidad":    None,
            "donante":   None,
            "resultado": "Sin conclusión",
            "accion":    None,
            "certeza":   0.0,
        }

    # Fase 3 — Subsistema de Explicación
    explicacion = _generar_explicacion(datos, hechos, decision, reglas_activadas)

    return {
        "unidad":           decision.get("unidad"),
        "donante":          decision.get("donante"),
        "resultado":        decision.get("resultado"),
        "accion":           decision.get("accion"),
        "certeza":          decision.get("certeza", 0.0),
        "sco_etiqueta":     hechos.get("sco_inicial"),
        "reglas_activadas": [r["id"] for r in reglas_activadas],
        "explicacion":      explicacion,
    }


# ---------------------------------------------------------------------------
# Subsistema de Explicación
# ---------------------------------------------------------------------------

def _generar_explicacion(datos, hechos, decision, reglas_activadas):
    """
    Genera la narrativa de trazabilidad de la decisión.
    Incluye: clasificación S/CO, certeza difusa, reglas disparadas con su
    justificación científica, y la decisión final estructurada.
    """
    lineas = []
    sep = "=" * 62

    lineas.append(sep)
    lineas.append("  SUBSISTEMA DE EXPLICACIÓN — TRAZABILIDAD DE DECISIÓN")
    lineas.append(sep)

    # Datos del análisis
    marcador = datos.get("marcador", "N/A")
    lineas.append(f"  Marcador evaluado : {marcador}")

    sco_val = datos.get("sco_inicial_valor")
    if sco_val is not None:
        etiqueta = hechos.get("sco_inicial", "N/A")
        certeza  = hechos.get("certeza_sco", 0.0)
        lineas.append(f"  S/CO inicial      : {sco_val:.2f}  →  [{etiqueta}]  "
                      f"(Certeza fuzzy: {certeza:.1f} %)")

    sco_rep_val = datos.get("sco_rep_valor")
    if sco_rep_val is not None:
        etiqueta_rep = hechos.get("sco_repeticion", "N/A")
        lineas.append(f"  S/CO repetición   : {sco_rep_val:.2f}  →  [{etiqueta_rep}]")

    if datos.get("vdrl"):
        lineas.append(f"  VDRL              : {datos['vdrl']}")
    if datos.get("clia"):
        lineas.append(f"  CLIA              : {datos['clia']}")
    if datos.get("nat"):
        lineas.append(f"  NAT               : {datos['nat']}")

    calidad = datos.get("calidad_muestra", "Normal")
    if calidad != "Normal":
        lineas.append(f"  Calidad muestra   : {calidad}")

    lineas.append("")

    # Reglas disparadas
    lineas.append("  REGLAS DISPARADAS (en orden de evaluación clínica):")
    lineas.append("  " + "-" * 58)

    if not reglas_activadas:
        lineas.append("    (Ninguna regla específica disparada)")
    else:
        for i, regla in enumerate(reglas_activadas, 1):
            lineas.append(f"  [{i}] {regla['id']}")
            lineas.append(f"       {regla['justificacion']}")
            if regla.get("accion"):
                lineas.append(f"       → Acción requerida: {regla['accion']}")

    lineas.append("")

    # Decisión final
    lineas.append("  DECISIÓN FINAL:")
    lineas.append("  " + "-" * 58)

    if decision.get("resultado") == "Rechazo Técnico":
        lineas.append(f"  Estado unidad  : {decision.get('unidad', 'Cuarentena')}")
        lineas.append(f"  Resultado      : Rechazo Técnico — muestra no apta para análisis")

    elif decision.get("resultado") == "Pendiente":
        lineas.append(f"  Estado unidad  : Pendiente — se requiere acción adicional")
        lineas.append(f"  Acción         : {decision.get('accion')}")

    elif decision.get("unidad") == "Apta":
        lineas.append(f"  Estado unidad  : ✔ APTA para transfusión")
        lineas.append(f"  Estado donante : {decision.get('donante', 'Habilitado')}")

    else:
        lineas.append(f"  Estado unidad  : ✘ {decision.get('unidad', 'Descarte')}")
        lineas.append(f"  Estado donante : {decision.get('donante', 'N/A')}")
        if decision.get("accion"):
            lineas.append(f"  Acción         : {decision.get('accion')}")

    lineas.append(sep)

    return "\n".join(lineas)
