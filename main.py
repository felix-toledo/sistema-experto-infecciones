"""
Punto de entrada del Sistema Experto de Seguridad Transfusional.

Modos de uso:
    python main.py              → menú interactivo por consola
    python main.py caso.json    → evaluación directa desde archivo JSON
"""

import json
import os
import sys

from expert_system import evaluar_caso
from fuzzy_engine import fuzzificar_sco, MARCADORES_NAT

MARCADORES_VALIDOS = ["HIV", "HBV", "HCV", "Sífilis", "Chagas", "Brucelosis", "HTLV I/II"]


# ---------------------------------------------------------------------------
# Utilidades de I/O
# ---------------------------------------------------------------------------

def _pedir_opcion(mensaje, opciones):
    """Solicita al usuario que elija una opción válida. Reintenta si es inválida."""
    opciones_upper = [o.upper() for o in opciones]
    while True:
        resp = input(mensaje).strip().upper()
        if resp in opciones_upper:
            return resp
        print(f"    Entrada inválida. Opciones aceptadas: {', '.join(opciones)}")


def _pedir_sco(mensaje):
    """Solicita y valida un valor numérico S/CO (≥ 0)."""
    while True:
        try:
            valor = float(input(mensaje).strip().replace(",", "."))
            if valor < 0:
                print("    El valor S/CO no puede ser negativo.")
                continue
            return valor
        except ValueError:
            print("    Ingrese un número válido (ej: 0.5 / 1.0 / 3.75).")


def _imprimir_resultado(resultado):
    """Muestra el resultado formateado de un caso evaluado."""
    print()
    print(resultado["explicacion"])
    ids = ", ".join(resultado.get("reglas_activadas", [])) or "(ninguna)"
    print(f"  Reglas activadas : {ids}")
    print()


# ---------------------------------------------------------------------------
# Modos de ejecución
# ---------------------------------------------------------------------------

def modo_manual():
    """Flujo interactivo de ingreso de datos por consola."""
    print("\n" + "-" * 50)
    print("  EVALUACIÓN MANUAL")
    print("-" * 50)
    datos = {}

    # Calidad de muestra
    resp = _pedir_opcion(
        "  ¿Calidad de la muestra? [Normal / Hemolizada / Lipémica]: ",
        ["NORMAL", "HEMOLIZADA", "LIPÉMICA"],
    )
    mapa_calidad = {"NORMAL": "Normal", "HEMOLIZADA": "Hemolizada", "LIPÉMICA": "Lipémica"}
    datos["calidad_muestra"] = mapa_calidad[resp]

    # Si la muestra es inválida, no hace falta pedir más datos
    if datos["calidad_muestra"] != "Normal":
        return evaluar_caso(datos)

    # Marcador
    print(f"  Marcadores disponibles: {', '.join(MARCADORES_VALIDOS)}")
    while True:
        marcador = input("  Marcador a evaluar: ").strip()
        if marcador in MARCADORES_VALIDOS:
            datos["marcador"] = marcador
            break
        print(f"    Marcador no reconocido. Opciones: {', '.join(MARCADORES_VALIDOS)}")

    # Protocolo especial para Sífilis (VDRL → CLIA)
    if datos["marcador"] == "Sífilis":
        resp_vdrl = _pedir_opcion(
            "  ¿Resultado VDRL? [Reactivo / No Reactivo]: ", ["REACTIVO", "NO REACTIVO"]
        )
        datos["vdrl"] = "Reactivo" if resp_vdrl == "REACTIVO" else "No Reactivo"

        if datos["vdrl"] == "Reactivo":
            print("  → VDRL reactivo: por protocolo se requiere CLIA confirmatorio.")
            resp_clia = _pedir_opcion(
                "  ¿Resultado CLIA? [Reactivo / No Reactivo]: ", ["REACTIVO", "NO REACTIVO"]
            )
            datos["clia"] = "Reactivo" if resp_clia == "REACTIVO" else "No Reactivo"

        return evaluar_caso(datos)

    # S/CO inicial
    datos["sco_inicial_valor"] = _pedir_sco("  Valor S/CO inicial (ej: 0.5): ")

    # Zona Gris → pedir repetición
    etiqueta, _ = fuzzificar_sco(datos["sco_inicial_valor"])
    if etiqueta == "Zona Gris":
        print("  ⚠ S/CO en Zona Gris (0.9 – 1.1). Por protocolo se requiere repetición.")
        tiene_rep = _pedir_opcion("  ¿Dispone del resultado de repetición? [S / N]: ", ["S", "N"])
        if tiene_rep == "S":
            datos["sco_rep_valor"] = _pedir_sco("  Valor S/CO en repetición: ")

    # NAT (solo para HIV, HBV, HCV)
    if datos["marcador"] in MARCADORES_NAT:
        resp_nat = _pedir_opcion(
            "  ¿Resultado NAT? [Reactivo / No Reactivo]: ", ["REACTIVO", "NO REACTIVO"]
        )
        datos["nat"] = "Reactivo" if resp_nat == "REACTIVO" else "No Reactivo"

    # Riesgo conductual
    resp_riesgo = _pedir_opcion(
        "  ¿Donante con factor de riesgo conductual? [S / N]: ", ["S", "N"]
    )
    datos["riesgo"] = "Sí" if resp_riesgo == "S" else "No"

    return evaluar_caso(datos)


def modo_json(ruta):
    """Carga y evalúa uno o varios casos desde un archivo JSON."""
    if not os.path.isfile(ruta):
        print(f"\n  Error: No se encontró el archivo '{ruta}'.")
        return

    try:
        with open(ruta, encoding="utf-8") as f:
            contenido = json.load(f)
    except json.JSONDecodeError as e:
        print(f"\n  Error al parsear el JSON: {e}")
        return

    casos = contenido if isinstance(contenido, list) else [contenido]
    print(f"\n--- EVALUACIÓN DESDE JSON: {os.path.basename(ruta)} ({len(casos)} caso/s) ---")

    for i, caso in enumerate(casos, 1):
        nombre = caso.get("nombre", f"Caso {i}")
        print(f"\n[{i}] {nombre}")
        resultado = evaluar_caso(caso)
        _imprimir_resultado(resultado)


def modo_tests():
    """Delega en test_cases.ejecutar_suite() para correr la validación completa."""
    import test_cases
    test_cases.ejecutar_suite()


# ---------------------------------------------------------------------------
# Menú principal
# ---------------------------------------------------------------------------

def menu_principal():
    """Bucle del menú interactivo."""
    while True:
        print("\n" + "=" * 50)
        print("   SISTEMA EXPERTO — SEGURIDAD TRANSFUSIONAL (ITT)")
        print("=" * 50)
        print("  [1] Evaluación manual (datos por consola)")
        print("  [2] Cargar caso(s) desde archivo JSON")
        print("  [3] Ejecutar suite de tests automáticos")
        print("  [4] Salir")
        print("-" * 50)

        opcion = _pedir_opcion("  Opción: ", ["1", "2", "3", "4"])

        if opcion == "1":
            resultado = modo_manual()
            _imprimir_resultado(resultado)

        elif opcion == "2":
            ruta = input("  Ruta del archivo JSON: ").strip()
            modo_json(ruta)

        elif opcion == "3":
            modo_tests()

        elif opcion == "4":
            print("\n  Hasta luego.\n")
            break


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo CLI directo: python main.py archivo.json
        modo_json(sys.argv[1])
    else:
        menu_principal()
