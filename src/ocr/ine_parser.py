"""
Motor de extracción de datos para credencial de elector (INE/IFE).

Incluye:
- Normalización de líneas MRZ (TD1).
- Cálculo y validación de check digits MRZ.
- Parsing de nombre desde MRZ.
- Reconstrucción certera de CURP usando máscaras generadas desde MRZ.
- Limpieza de ruido OCR y corrección de errores por posición.

Nota: las funciones de OCR con PaddleOCR se mantienen como referencia;
el demo puede operar con texto plano ya extraído.
"""
import re

# ============================================================
# MRZ — Machine Readable Zone
# ============================================================

def normalizar_linea_mrz(texto: str) -> str:
    """Conserva solo A-Z, 0-9 y '<', reemplazando comunes errores OCR."""
    if not texto:
        return ""
    texto = str(texto).upper().strip()
    reemplazos = {" ": "<", "«": "<", "‹": "<", ">": "<", "|": "<"}
    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)
    return re.sub(r"[^A-Z0-9<]", "", texto)


def limpiar_filler_mrz(valor: str) -> str:
    """Quita caracteres de relleno '<'."""
    return str(valor or "").replace("<", "").strip()


def _valor_char_mrz(char: str) -> int:
    if char == "<":
        return 0
    if char.isdigit():
        return int(char)
    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10
    return 0


def calcular_check_digit_mrz(valor: str) -> str:
    """Check digit con pesos 7, 3, 1 (estándar ICAO 9303)."""
    pesos = [7, 3, 1]
    total = sum(
        _valor_char_mrz(c) * pesos[i % 3] for i, c in enumerate(valor)
    )
    return str(total % 10)


def parsear_nombre_mrz(linea3: str) -> dict:
    """
    APELLIDO1<APELLIDO2<<NOMBRE<NOMBRE2
    """
    linea3 = str(linea3 or "").rstrip("<")
    apellidos_raw, separador, nombres_raw = linea3.partition("<<")
    apellidos = [x for x in apellidos_raw.split("<") if x]
    nombres = [x for x in nombres_raw.split("<") if x]

    last_name = apellidos[0] if apellidos else ""
    last_name2 = " ".join(apellidos[1:]) if len(apellidos) > 1 else ""
    first_name = nombres[0] if nombres else ""
    first_name2 = " ".join(nombres[1:]) if len(nombres) > 1 else ""

    full_name = " ".join(
        p for p in [last_name, last_name2, first_name, first_name2] if p
    )
    return {
        "last_name": last_name,
        "last_name2": last_name2,
        "spacing": separador,
        "first_name": first_name,
        "first_name2": first_name2,
        "full_name": full_name,
    }


def validar_check_digits_mrz_td1(linea1: str, linea2: str) -> dict:
    """Valida los 4 check digits del MRZ TD1. No bloqueante."""
    doc_number = linea1[5:14]
    doc_check = linea1[14]
    birth_date = linea2[0:6]
    birth_check = linea2[6]
    expiration_date = linea2[8:14]
    expiration_check = linea2[14]
    composite_data = linea1[5:30] + linea2[0:7] + linea2[8:15] + linea2[18:29]
    composite_check = linea2[29]

    return {
        "doc_number_check_valid": calcular_check_digit_mrz(doc_number) == doc_check,
        "birth_check_valid": calcular_check_digit_mrz(birth_date) == birth_check,
        "expiration_check_valid": calcular_check_digit_mrz(expiration_date) == expiration_check,
        "composite_check_valid": calcular_check_digit_mrz(composite_data) == composite_check,
    }


def parsear_mrz_ine(lineas_mrz: list) -> dict:
    """Parsea 3 líneas MRZ TD1 de INE mexicana."""
    if not lineas_mrz or len(lineas_mrz) != 3:
        return {
            "mrz_detected": False,
            "mrz_format_valid": False,
            "error": "No se detectaron 3 líneas MRZ",
            "mrz_raw": lineas_mrz or [],
            "dataOcr": {},
            "mrzDerived": {},
            "mrzCheckDigits": {},
        }

    l1 = normalizar_linea_mrz(lineas_mrz[0]).ljust(30, "<")[:30]
    l2 = normalizar_linea_mrz(lineas_mrz[1]).ljust(30, "<")[:30]
    l3 = normalizar_linea_mrz(lineas_mrz[2]).ljust(30, "<")[:30]

    nombre_data = parsear_nombre_mrz(l3)
    check_digits = validar_check_digits_mrz_td1(l1, l2)
    mrz_format_valid = l1.startswith("IDMEX") and len(l1) == 30 and len(l2) == 30 and len(l3) == 30

    data_ocr = {
        "type": limpiar_filler_mrz(l1[0:2]),
        "issue_country": limpiar_filler_mrz(l1[2:5]),
        "doc_number": limpiar_filler_mrz(l1[5:14]),
        "check_sum": l1[14],
        "first_optional": limpiar_filler_mrz(l1[15:30]),
        "date_birth": l2[0:6],
        "birth_check": l2[6],
        "sex": "" if l2[7] == "<" else l2[7],
        "expiration_date": l2[8:14],
        "nacionality": limpiar_filler_mrz(l2[15:18]),
        "second_optional": limpiar_filler_mrz(l2[18:29]),
        "check_digit": l2[29],
        "last_name": nombre_data["last_name"],
        "last_name2": nombre_data["last_name2"],
        "spacing": nombre_data["spacing"],
        "first_name": nombre_data["first_name"],
        "first_name2": nombre_data["first_name2"],
        "full_name": nombre_data["full_name"],
    }

    return {
        "mrz_detected": True,
        "mrz_format_valid": mrz_format_valid,
        "mrz_raw": {"line1": l1, "line2": l2, "line3": l3},
        "dataOcr": data_ocr,
        "mrzDerived": {
            "cic": limpiar_filler_mrz(l1[5:14]),
            "identificador_ciudadano": limpiar_filler_mrz(l1[15:30]),
        },
        "mrzCheckDigits": check_digits,
    }


# ============================================================
# CURP — Reconstrucción certera con máscara MRZ
# ============================================================

def normalizar_nombre_curp(texto: str) -> str:
    if not texto:
        return ""
    texto = str(texto).upper().strip()
    reemplazos = {"Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ü": "U", "Ñ": "X"}
    for o, d in reemplazos.items():
        texto = texto.replace(o, d)
    return re.sub(r"[^A-Z\s]", " ", texto).strip()


def _primera_vocal_interna(palabra: str) -> str:
    p = normalizar_nombre_curp(palabra).replace(" ", "")
    if len(p) <= 1:
        return ""
    for c in p[1:]:
        if c in "AEIOU":
            return c
    return ""


def _primera_consonante_interna(palabra: str) -> str:
    p = normalizar_nombre_curp(palabra).replace(" ", "")
    if len(p) <= 1:
        return ""
    for c in p[1:]:
        if c in "BCDFGHJKLMNPQRSTVWXYZ":
            return c
    return ""


def _nombre_pila(nombres: list) -> str:
    prohibidos = {"JOSE", "J", "J.", "MARIA", "MA", "MA."}
    if nombres and nombres[0] in prohibidos and len(nombres) > 1:
        return nombres[1]
    return nombres[0] if nombres else ""


def construir_mascara_curp(datos_extraidos: dict) -> list:
    """
    Construye máscara de 18 posiciones usando datos conocidos del MRZ.
    Posiciones desconocidas (entidad, homoclave) se dejan en None.
    """
    data_ocr = datos_extraidos.get("dataOcr", {}) or {}
    componentes = _obtener_componentes_nombre(datos_extraidos)
    if not componentes:
        return None

    paterno = componentes["paterno"]
    materno = componentes["materno"]
    nombre = componentes["nombre"]
    if not paterno or not materno or not nombre:
        return None

    fecha = str(data_ocr.get("date_birth") or "").strip()
    sexo = data_ocr.get("sex", "")
    # MRZ: M=Hombre, F=Mujer → CURP: H/M
    sexo_curp = "H" if sexo == "M" else ("M" if sexo == "F" else "")

    mascara = [None] * 18
    mascara[0] = paterno[0]
    mascara[1] = _primera_vocal_interna(paterno)
    mascara[2] = materno[0]
    mascara[3] = nombre[0]

    if len(fecha) == 6 and re.fullmatch(r"[0-9]{6}", fecha):
        for i, ch in enumerate(fecha):
            mascara[4 + i] = ch

    if sexo_curp:
        mascara[10] = sexo_curp

    mascara[13] = _primera_consonante_interna(paterno)
    mascara[14] = _primera_consonante_interna(materno)
    mascara[15] = _primera_consonante_interna(nombre)

    return mascara


def _obtener_componentes_nombre(datos_extraidos: dict) -> dict:
    data_ocr = datos_extraidos.get("dataOcr", {}) or {}
    paterno = normalizar_nombre_curp(data_ocr.get("last_name"))
    materno = normalizar_nombre_curp(data_ocr.get("last_name2"))
    first_name = normalizar_nombre_curp(data_ocr.get("first_name"))
    first_name2 = normalizar_nombre_curp(data_ocr.get("first_name2"))

    if paterno and materno and first_name:
        nombres = [first_name, first_name2] if first_name2 else [first_name]
        return {
            "paterno": paterno,
            "materno": materno,
            "nombre": _nombre_pila(nombres),
        }

    # Fallback: partir nombre completo
    nombre_completo = normalizar_nombre_curp(datos_extraidos.get("nombre"))
    if not nombre_completo:
        return None
    partes = [p for p in nombre_completo.split() if p not in {"DE", "DEL", "LA", "LAS", "LOS", "Y"}]
    if len(partes) < 3:
        return None
    return {
        "paterno": partes[0],
        "materno": partes[1],
        "nombre": _nombre_pila(partes[2:]),
    }


def _equivalentes_ocr(char: str) -> set:
    char = str(char or "").upper()
    mapa = {
        "A": {"A", "4"}, "B": {"B", "8"}, "C": {"C", "O", "0"},
        "D": {"D", "O", "0"}, "G": {"G", "6"}, "I": {"I", "1", "L"},
        "L": {"L", "1", "I"}, "O": {"O", "0", "D", "Q"},
        "Q": {"Q", "0", "O"}, "S": {"S", "5"}, "T": {"T", "7"},
        "Z": {"Z", "2"}, "0": {"0", "O", "D", "Q"}, "1": {"1", "I", "L"},
        "2": {"2", "Z"}, "5": {"5", "S"}, "6": {"6", "G"}, "7": {"7", "T"},
        "8": {"8", "B"},
    }
    return mapa.get(char, {char})


def _chars_equivalentes(esperado, leido) -> bool:
    return str(leido or "").upper() in _equivalentes_ocr(str(esperado or "").upper())


def evaluar_candidato_curp(candidato: str, mascara: list, prioridad: int = 1) -> int:
    if not candidato or len(candidato) != 18 or not mascara:
        return -999

    score = 0
    conocidas = 0
    for i, esperado in enumerate(mascara):
        if not esperado:
            continue
        conocidas += 1
        if _chars_equivalentes(esperado, candidato[i]):
            score += 3
        else:
            score -= 2

    # Fecha básica
    digitos_fecha = sum(1 for c in candidato[4:10] if c.isdigit())
    score += 3 if digitos_fecha >= 5 else (1 if digitos_fecha >= 4 else -5)

    # Sexo
    score += 2 if candidato[10] in {"H", "M", "N", "0"} else -3

    # Último dígito
    score += 2 if candidato[17].isdigit() else -2

    score += prioridad

    # Penalizaciones estructurales
    prefix_match = sum(
        1 for i in range(4)
        if mascara[i] and _chars_equivalentes(mascara[i], candidato[i])
    )
    if prefix_match < 3:
        score -= 12

    internas_match = sum(
        1 for i in range(13, 16)
        if mascara[i] and _chars_equivalentes(mascara[i], candidato[i])
    )
    if internas_match < 2:
        score -= 8

    return score


def corregir_curp_con_mascara(candidato: str, mascara: list) -> str:
    curp = list(candidato.upper())
    for i, esperado in enumerate(mascara):
        if esperado:
            curp[i] = esperado
    return "".join(curp)


def buscar_curp_certero(textos_frontales: list, datos_extraidos: dict):
    """
    Busca la CURP más probable usando candidatos OCR + máscara MRZ.
    Retorna (curp_corregida, metadata).
    """
    mascara = construir_mascara_curp(datos_extraidos)
    if not mascara:
        return None, {"reason": "No se pudo construir máscara CURP"}

    candidatos = []
    vistos = set()
    texto_total = "".join(str(t or "").upper() for t in textos_frontales)
    texto_total_norm = re.sub(r"[^A-Z0-9]", "", texto_total)

    # Regex bruto
    for c in re.findall(r"[A-Z0-9]{18}", texto_total_norm):
        if c not in vistos:
            vistos.add(c)
            candidatos.append({"valor": c, "prioridad": 1})

    mejor = None
    mejor_score = -999
    for item in candidatos:
        sc = evaluar_candidato_curp(item["valor"], mascara, item.get("prioridad", 1))
        if sc > mejor_score:
            mejor_score = sc
            mejor = item

    conocidas = sum(1 for c in mascara if c)
    umbral = max(24, conocidas * 2 - 4)

    if not mejor or mejor_score < umbral:
        return None, {
            "best_candidate": mejor["valor"] if mejor else None,
            "best_score": mejor_score,
            "threshold": umbral,
            "reason": "Ningún candidato superó el umbral de confianza",
        }

    curp_final = corregir_curp_con_mascara(mejor["valor"], mascara)
    return curp_final, {
        "best_candidate": mejor["valor"],
        "best_score": mejor_score,
        "threshold": umbral,
        "reason": "CURP detectado por máscara MRZ/dataOcr",
    }
