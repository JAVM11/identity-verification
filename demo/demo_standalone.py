"""
Demo standalone del motor de parsing IDVE.
No requiere Flask, GPU, MySQL ni modelos de deep learning.
Ejecuta la lógica pura de MRZ y CURP.
"""
from src.ocr.ine_parser import parsear_mrz_ine, buscar_curp_certero


def demo_mrz():
    print("=" * 60)
    print("DEMO 1: Parseo de MRZ TD1 (INE Mexicana)")
    print("=" * 60)

    # MRZ de ejemplo basado en formato real
    lineas = [
        "IDMEX1234567890<<<<<<<<<<<<<<<",  # Línea 1: IDMEX + CIC + identificador
        "0000000H0000000MEX<<<<<<<<<<<0",  # Línea 2: fecha nac, sexo, expiración, nacionalidad
        "GARCIA<<LOPEZ<<JUAN<PEDRO<<<<<",  # Línea 3: apellidos y nombres
    ]

    resultado = parsear_mrz_ine(lineas)
    print("\nMRZ detectado:", resultado["mrz_detected"])
    print("Formato válido:", resultado["mrz_format_valid"])
    print("\n--- dataOcr ---")
    for k, v in resultado["dataOcr"].items():
        print(f"  {k}: {v}")
    print("\n--- Check Digits ---")
    for k, v in resultado["mrzCheckDigits"].items():
        print(f"  {k}: {v}")


def demo_curp():
    print("\n" + "=" * 60)
    print("DEMO 2: Reconstrucción de CURP con máscara MRZ")
    print("=" * 60)

    # Simulamos que el OCR frontal leyó esto (con ruido y errores)
    textos_frontales = [
        "INSTITUTO NACIONAL ELECTORAL",
        "NOMBRE GARCIA LOPEZ JUAN PEDRO",
        "FECHA DE NACIMIENTO 21/11/2000",
        "SEXO H",
        "CURP: GARJ001121HDFLRN09",  # candidato real
        "GARJ001121HDFLRN09",         # otro candidato sin etiqueta
    ]

    # Datos que ya obtuvimos del reverso (MRZ)
    datos_extraidos = {
        "dataOcr": {
            "last_name": "GARCIA",
            "last_name2": "LOPEZ",
            "first_name": "JUAN",
            "first_name2": "PEDRO",
            "date_birth": "001121",  # YYMMDD
            "sex": "M",  # MRZ: M = Hombre
        },
        "nombre": "GARCIA LOPEZ JUAN PEDRO",
    }

    curp, meta = buscar_curp_certero(textos_frontales, datos_extraidos)

    print("\nCandidatos revisados:", meta.get("candidates_checked", "N/A"))
    print("Mejor score:", meta.get("best_score"))
    print("Umbral:", meta.get("threshold"))
    print("CURP reconstruida:", curp)
    print("Razón:", meta.get("reason"))


if __name__ == "__main__":
    demo_mrz()
    demo_curp()
    print("\n✅ Demo completado sin dependencias de GPU ni OCR.")
