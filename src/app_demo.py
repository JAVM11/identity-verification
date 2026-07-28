"""
Aplicación Flask de demostración — IDVE Identity Verification.

Versión simplificada del backend productivo. No requiere MySQL ni GPU.
Muestra la estructura de endpoints, validaciones y respuestas estandarizadas.
"""
import os
import uuid
from flask import Flask, request, jsonify

from src.config import UPLOAD_FOLDER, LOG_FOLDER
from src.auth.jwt_handler import generar_token, validar_token
from src.ocr.ine_parser import parsear_mrz_ine, buscar_curp_certero

app = Flask(__name__)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)


# ── Helpers de respuesta ──

def respuesta_error(codigo: int, mensaje: str, http_status: int = 400, detail=None):
    body = {"codigo": codigo, "status": "FAILED", "error": {"message": mensaje}}
    if detail:
        body["error"]["detail"] = detail
    return jsonify(body), http_status


def respuesta_verifica(
    codigo: int,
    status: str = "FAILED",
    result: int = 0,
    errors=None,
    identity=None,
    data_ocr=None,
    face_result: bool = False,
    similarity=None,
    http_status: int = 200,
):
    if errors is None:
        errors = []
    if identity is None:
        identity = {"fullName": "", "curp": "", "cic": "", "urlVigencia": ""}
    if data_ocr is None:
        data_ocr = {}
    return jsonify({
        "codigo": codigo,
        "respuestaverifica": {
            "status": status,
            "result": result,
            "errors": errors,
            "identity": identity,
            "dataOcr": data_ocr,
            "faceComparison": {
                "result": face_result,
                "similarity": similarity,
            },
        }
    }), http_status


# ── Endpoints ──

@app.route("/", methods=["GET"])
def healthcheck():
    return jsonify({"status": "IDVE Showcase activo", "version": "1.0.0-demo"})


@app.route("/auth/token", methods=["POST"])
def auth_token():
    """
    Demo de generación JWT. No valida contra base de datos.
    Body: { "tenant_code": "DEMO", "environment": "sandbox", "username": "demo@idve.mx" }
    """
    data = request.get_json(silent=True) or request.form or {}
    tenant_code = str(data.get("tenant_code") or data.get("Empresa") or "").strip().upper()
    environment = str(data.get("environment") or "sandbox").strip().lower()
    username = str(data.get("username") or data.get("correo") or "").strip().lower()

    if not tenant_code:
        return jsonify({"codigo": 400, "status": "FAILED", "message": "tenant_code requerido"}), 400
    if environment not in {"sandbox", "production"}:
        return jsonify({"codigo": 400, "status": "FAILED", "message": "environment inválido"}), 400
    if not username:
        return jsonify({"codigo": 400, "status": "FAILED", "message": "username requerido"}), 400

    token = generar_token({
        "tenant_code": tenant_code,
        "environment": environment,
        "username": username,
        "scopes": ["verification.create", "verification.read", "face.match"],
    })

    return jsonify({
        "codigo": 200,
        "status": "FINISH",
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
    })


@app.route("/auth/validate", methods=["GET", "POST"])
def auth_validate():
    """Valida un token JWT vía header Authorization: Bearer <token>."""
    auth = request.headers.get("Authorization", "")
    parts = auth.split()
    token = parts[1] if len(parts) == 2 and parts[0].lower() == "bearer" else None

    if not token:
        data = request.get_json(silent=True) or request.form or {}
        token = data.get("access_token")

    if not token:
        return jsonify({"codigo": 401, "descripcion": "Token inválido"}), 401

    ok, payload, error = validar_token(token)
    if not ok:
        return jsonify({"codigo": 401, "descripcion": f"Token inválido: {error}"}), 401

    return jsonify({"codigo": 200, "descripcion": "Token válido", "claims": payload})


@app.route("/api/procesarRostros", methods=["POST"])
def procesar_rostros():
    """
    Comparación facial 1:1 directa.
    Recibe: rostro1, rostro2 (multipart/form-data).
    En demo solo valida recepción y retorna estructura; no ejecuta modelos.
    """
    if "rostro1" not in request.files or "rostro2" not in request.files:
        return respuesta_error(400, "Se requieren rostro1 y rostro2")

    # Demo: guardamos archivos pero no corremo inferencia para no depender de GPU/libs pesadas.
    f1 = request.files["rostro1"]
    f2 = request.files["rostro2"]
    n1 = f"{uuid.uuid4()}_{f1.filename}"
    n2 = f"{uuid.uuid4()}_{f2.filename}"
    f1.save(os.path.join(UPLOAD_FOLDER, n1))
    f2.save(os.path.join(UPLOAD_FOLDER, n2))

    return jsonify({
        "codigo": 200,
        "descripcion": "Imágenes recibidas correctamente (modo demo, sin inferencia)",
        "distancia": None,
        "archivos": {"rostro1": n1, "rostro2": n2},
    })


@app.route("/api/procesarIneJuntoRostro", methods=["POST"])
def procesar_ine_junto_rostro():
    """
    Pipeline completo de demostración.
    Recibe INE frontal, reverso y referencia de rostro.
    En modo demo valida estructura y retorna formato de respuesta productivo.
    """
    if "INEFrontal" not in request.files:
        return respuesta_verifica(
            codigo=400,
            errors=[{"code": "MISSING_INE_FRONTAL", "message": "Falta INEFrontal"}],
            http_status=400,
        )
    if "INEReverso" not in request.files:
        return respuesta_verifica(
            codigo=400,
            errors=[{"code": "MISSING_INE_REVERSO", "message": "Falta INEReverso"}],
            http_status=400,
        )
    if "Rostro" not in request.form:
        return respuesta_verifica(
            codigo=400,
            errors=[{"code": "MISSING_ROSTRO", "message": "Falta Rostro"}],
            http_status=400,
        )

    # Guardar archivos de demo
    frontal = request.files["INEFrontal"]
    reverso = request.files["INEReverso"]
    nf = f"{uuid.uuid4()}_{frontal.filename}"
    nr = f"{uuid.uuid4()}_{reverso.filename}"
    frontal.save(os.path.join(UPLOAD_FOLDER, nf))
    reverso.save(os.path.join(UPLOAD_FOLDER, nr))

    # Respuesta de demo: muestra la estructura exacta que usa producción
    return respuesta_verifica(
        codigo=200,
        status="FINISH",
        result=100,
        errors=[{"code": "DEMO_MODE", "message": "Este es un endpoint de demostración. No se ejecutó inferencia real."}],
        identity={
            "fullName": "DEMO NAME",
            "curp": "DEMO000000HDFLLL00",
            "cic": "12345678",
            "identificador_ciudadano": "12345678901",
            "urlVigencia": "",
        },
        data_ocr={
            "type": "ID", "subtype": "", "issue_country": "MEX",
            "doc_number": "12345678", "check_sum": "0",
            "first_optional": "12345678901", "date_birth": "000000",
            "birth_check": "0", "sex": "H", "expiration_date": "000000",
            "nacionality": "MEX", "second_optional": "", "check_digit": "0",
            "last_name": "DEMO", "last_name2": "", "spacing": "",
            "first_name": "NAME", "first_name2": "",
        },
        face_result=True,
        similarity=0.3842,
    )


@app.route("/demo/mrz-parse", methods=["POST"])
def demo_mrz_parse():
    """
    Endpoint utilitario para probar el parser de MRZ sin OCR.
    Body JSON: { "lineas": ["IDMEX1234567890<<<<<<<<<<<<<<<", "0000000H0000000MEX<<<<<<<<<<<0", "APELLIDO<<NOMBRE<NOMBRE2<<<<<"] }
    """
    data = request.get_json(silent=True) or {}
    lineas = data.get("lineas", [])
    if len(lineas) != 3:
        return jsonify({"error": "Se requieren exactamente 3 líneas MRZ"}), 400

    resultado = parsear_mrz_ine(lineas)
    return jsonify(resultado)


@app.route("/demo/curp-reconstruct", methods=["POST"])
def demo_curp_reconstruct():
    """
    Endpoint utilitario para probar la reconstrucción de CURP.
    Body JSON: {
        "textos_frontales": ["CURP: LOGR021121HDFLLLA8", "NOMBRE: LUIS OMAR"],
        "datos_extraidos": { "dataOcr": { ... }, "nombre": "..." }
    }
    """
    data = request.get_json(silent=True) or {}
    textos = data.get("textos_frontales", [])
    datos = data.get("datos_extraidos", {})

    curp, meta = buscar_curp_certero(textos, datos)
    return jsonify({"curp": curp, "metadata": meta})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
