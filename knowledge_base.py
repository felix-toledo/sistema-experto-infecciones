"""
Base de Conocimientos del Sistema Experto de Seguridad Transfusional.
Contiene las reglas extraídas del experto (Tabla P->A).

Clave "prioridad": orden de evaluación clínica (mayor número = mayor prioridad).
Las reglas sin "unidad" son acciones intermedias que no producen decisión final.
"""

REGLAS = [
    # -----------------------------------------------------------------------
    # R1 — Todo negativo → Apta  (menor prioridad: solo cuando nada más dispara)
    # -----------------------------------------------------------------------
    {
        "id": "R1",
        "prioridad": 1,
        "condiciones": {"sco": "No Reactivo", "nat": "No Reactivo", "riesgo": "No"},
        "unidad": "Apta",
        "donante": "Habilitado",
        "justificacion": "Tamizaje negativo completo y ausencia de factores de riesgo epidemiológico."
    },
    # -----------------------------------------------------------------------
    # R2_* — Zona Gris inicial: acción intermedia diferenciada por certeza difusa
    # Las tres variantes son mutuamente excluyentes y no producen decisión final.
    # -----------------------------------------------------------------------
    {
        "id": "R2_alta_certeza",
        "prioridad": 16,
        "condiciones": {
            "sco_inicial": "Zona Gris",
            "certeza_sco": lambda v: v is not None and v >= 45,
        },
        "accion": "Repetir análisis por duplicado",
        "justificacion": "Todo valor entre 0.9 y 1.1 requiere confirmación técnica inmediata."
    },
    {
        "id": "R2_baja_certeza",
        "prioridad": 16,
        "condiciones": {
            "sco_inicial": "Zona Gris",
            "certeza_sco": lambda v: v is not None and 30 <= v < 45,
        },
        "accion": "Pedir nueva muestra (Baja certeza técnica)",
        "justificacion": "El S/CO cae en la banda de baja certeza (30 % ≤ certeza < 45 %). Se solicita nueva muestra antes de repetir."
    },
    {
        "id": "R2_critica",
        "prioridad": 16,
        "condiciones": {
            "sco_inicial": "Zona Gris",
            "certeza_sco": lambda v: v is not None and v < 30,
        },
        "accion": "Solicitar nueva muestra del donante (certeza técnica insuficiente — valor próximo al límite Reactivo)",
        "justificacion": "El S/CO cae cerca del umbral Reactivo (certeza < 30 %). La certeza técnica es insuficiente para un análisis por duplicado."
    },
    # -----------------------------------------------------------------------
    # R3 — Zona Gris + repetición No Reactivo → Descarte por precaución
    # -----------------------------------------------------------------------
    {
        "id": "R3",
        "prioridad": 12,
        "condiciones": {"sco_inicial": "Zona Gris", "repeticion": "No Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "Serología Dudosa: Ante una duda inicial, se descarta por seguridad aunque la repetición sea negativa."
    },
    # -----------------------------------------------------------------------
    # R4 — NAT reactivo (ventana serológica) → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R4",
        "prioridad": 11,
        "condiciones": {"nat": "Reactivo"},  # Aplica a HIV, HBV, HCV
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Detección directa de ácidos nucleicos; indica infección activa o periodo de ventana."
    },
    # -----------------------------------------------------------------------
    # R5 — SCO + NAT ambos reactivos → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R5",
        "prioridad": 10,
        "condiciones": {"sco": "Reactivo", "nat": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Infección confirmada por serología y biología molecular."
    },
    # -----------------------------------------------------------------------
    # R6 — SCO no reactivo pero con riesgo conductual → Diferido Temporal
    # -----------------------------------------------------------------------
    {
        "id": "R6",
        "prioridad": 2,
        "condiciones": {"sco": "No Reactivo", "riesgo": "Sí"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "Principio de precaución: El riesgo conductual invalida el negativo por posible ventana silente."
    },
    # -----------------------------------------------------------------------
    # R7 — SCO reactivo, NAT no reactivo → Permanente (seguridad del receptor)
    # -----------------------------------------------------------------------
    {
        "id": "R7",
        "prioridad": 9,
        "condiciones": {"sco": "Reactivo", "nat": "No Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Reactividad serológica persistente; se prioriza la seguridad del receptor de la unidad."
    },
    # -----------------------------------------------------------------------
    # R8 — Sífilis VDRL reactivo → solicitar CLIA (acción intermedia)
    # -----------------------------------------------------------------------
    {
        "id": "R8",
        "prioridad": 19,
        "condiciones": {"marcador": "Sífilis", "vdrl": "Reactivo"},
        "accion": "Realizar CLIA confirmatorio",
        "justificacion": "Algoritmo tradicional: Se requiere prueba treponémica para confirmar sospecha de VDRL."
    },
    # -----------------------------------------------------------------------
    # R9 — Sífilis: VDRL + CLIA reactivos → Diferido Temporal
    # -----------------------------------------------------------------------
    {
        "id": "R9",
        "prioridad": 18,
        "condiciones": {"vdrl": "Reactivo", "clia": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "Infección por Sífilis confirmada. Requiere tratamiento y alta médica para reingreso."
    },
    # -----------------------------------------------------------------------
    # R10 — Sífilis: cicatriz serológica (VDRL neg, CLIA pos) → Diferido Temporal
    # -----------------------------------------------------------------------
    {
        "id": "R10",
        "prioridad": 17,
        "condiciones": {"vdrl": "No Reactivo", "clia": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "Cicatriz serológica o infección muy temprana. La unidad no es apta para transfusión."
    },
    # -----------------------------------------------------------------------
    # R11 — Chagas reactivo → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R11",
        "prioridad": 8,
        "condiciones": {"marcador": "Chagas", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Serología reactiva para Chagas es vinculante para el descarte definitivo de la bolsa."
    },
    # -----------------------------------------------------------------------
    # R12 — HTLV I/II reactivo → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R12",
        "prioridad": 7,
        "condiciones": {"marcador": "HTLV I/II", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Reactividad para HTLV implica exclusión permanente del donante de sangre."
    },
    # -----------------------------------------------------------------------
    # R13 — Zona Gris + NAT reactivo → confirma infección → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R13",
        "prioridad": 15,
        "condiciones": {"sco": "Zona Gris", "nat": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "La biología molecular confirma que la duda serológica es una infección real."
    },
    # -----------------------------------------------------------------------
    # R14 — Brucelosis reactiva → Diferido Temporal
    # -----------------------------------------------------------------------
    {
        "id": "R14",
        "prioridad": 6,
        "condiciones": {"marcador": "Brucelosis", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "Al igual que la Sífilis, permite reingreso con certificado de tratamiento y alta médica."
    },
    # -----------------------------------------------------------------------
    # R15 — HCV reactivo → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R15",
        "prioridad": 5,
        "condiciones": {"marcador": "HCV", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Hepatitis C confirmada por serología; descarte y notificación obligatoria."
    },
    # -----------------------------------------------------------------------
    # R16 — HBV reactivo → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R16",
        "prioridad": 4,
        "condiciones": {"marcador": "HBV", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Hepatitis B detectada; bloqueo definitivo del donante en el registro nacional."
    },
    # -----------------------------------------------------------------------
    # R17 — HIV reactivo → Permanente
    # -----------------------------------------------------------------------
    {
        "id": "R17",
        "prioridad": 3,
        "condiciones": {"marcador": "HIV", "sco": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Resultado reactivo para VIH; requiere derivación a infectología y descarte de unidad."
    },
    # -----------------------------------------------------------------------
    # R18 — Repetición también Zona Gris → Diferido Temporal por protocolo
    # -----------------------------------------------------------------------
    {
        "id": "R18",
        "prioridad": 14,
        "condiciones": {"sco_repeticion": "Zona Gris"},
        "unidad": "Descarte",
        "donante": "Diferido Temporal",
        "justificacion": "La persistencia de valores indeterminados inhabilita la unidad por protocolo de seguridad."
    },
    # -----------------------------------------------------------------------
    # R19 — Repetición reactiva → Diferido Permanente confirmado
    # -----------------------------------------------------------------------
    {
        "id": "R19",
        "prioridad": 13,
        "condiciones": {"sco_repeticion": "Reactivo"},
        "unidad": "Descarte",
        "donante": "Diferido Permanente",
        "justificacion": "Confirmación de reactividad serológica tras re-testeo."
    },
    # -----------------------------------------------------------------------
    # R20 — Rechazo técnico (mayor prioridad: corta toda evaluación)
    # -----------------------------------------------------------------------
    {
        "id": "R20",
        "prioridad": 20,
        "condiciones": {"calidad_muestra": "Hemolizada o Lipémica"},
        "resultado": "Rechazo Técnico",
        "unidad": "Cuarentena",
        "justificacion": "Interferencia: La calidad de la muestra impide una lectura óptica confiable en el analizador."
    },
]