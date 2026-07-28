# IDVE — Identity Verification Engine

> Backend de verificación de identidad biométrica 1:1 con OCR de documentos mexicanos (INE/IFE).

Este proyecto es el motor de inferencia de un sistema de validación de identidad. Procesa credenciales de elector y rostros reales para confirmar que el documento pertenece a la persona que lo presenta.

---

## Qué hace

- **Comparación facial 1:1** entre rostro en INE y rostro en vivo.
- **OCR espacial** con PaddleOCR para leer textos de alta variabilidad.
- **Extracción de MRZ** del reverso de la credencial (formato TD1).
- **Reconstrucción de CURP** usando máscaras generadas desde datos MRZ + heurísticas OCR.
- **Validación de check-digits** MRZ para detectar credenciales alteradas.
- **Autenticación multi-tenant** con JWT y control de scopes por ambiente.

---

## Arquitectura

```
Request (multipart/form-data)
    ├── INE Frontal  →  Detección de rostro + OCR (nombre, CURP, domicilio)
    ├── INE Reverso  →  Lectura MRZ + QR de vigencia
    └── Rostro Real  →  Encoding facial 128-D
              ↓
    Comparación facial (face_recognition + MediaPipe landmarks)
              ↓
    Extracción estructurada (MRZ → dataOcr → CURP → identity)
              ↓
    Respuesta JSON con códigos lógicos
```

---

## Tech Stack

| Capa | Tecnología |
|------|-----------|
| API | Flask |
| Visión | OpenCV, MediaPipe FaceMesh, face_recognition |
| OCR | PaddleOCR / PaddlePaddle (GPU) |
| QR | QReader |
| Auth | PyJWT + MySQL (tenant isolation) |
| Deploy | Docker + GPU support |

---

## Instalación (modo demo)

```bash
git clone https://github.com/JAVM11/idve-identity-verification.git
cd idve-identity-verification
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Correr la API demo (sin GPU ni DB)
```bash
python src/app_demo.py
```

### Correr el demo standalone (solo lógica de parsing)
```bash
python demo/demo_standalone.py
```

---

## Endpoints principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET`  | `/` | Healthcheck |
| `POST` | `/api/procesarIneJuntoRostro` | Pipeline completo INE + Rostro |
| `POST` | `/api/procesarRostros` | Comparación facial 1:1 directa |
| `POST` | `/auth/token` | Generación de JWT |
| `POST` | `/crearusuario` | Alta de tenant + usuario + scopes |

> Ver documentación completa en [`docs/ENDPOINTS.md`](docs/ENDPOINTS.md).

---

## Lógica de negocio destacada

### Reconstrucción de CURP 
En lugar de confiar ciegamente en OCR, el sistema:
1. Extrae nombre, fecha y sexo desde el MRZ del reverso.
2. Construye una **máscara de 18 posiciones** con los caracteres conocidos.
3. Busca candidatos de CURP en el OCR frontal.
4. Puntúa cada candidato contra la máscara (posiciones 1-4, 5-10, 11, 14-16).
5. Corrige errores de lectura OCR por posición (O→0, I→1, etc.).

### Códigos lógicos (ejemplos)
| Código | Significado |
|--------|-------------|
| `200` | OK — misma persona, datos completos. |
| `201` | OK — misma persona, datos OCR con advertencias. |
| `203` | Fallo — no es la misma persona. |
| `204` | Fallo — no se detectó rostro o landmarks. |
| `205` | Fallo — imagen de rostro no encontrada en servidor. |

---

## Nota sobre este repositorio

Este es un **repositorio de showcase**. La versión productiva incluye:
- Pool de conexiones MySQL con cifrado de columnas (email_hash, password_hash).
- Control de intentos de login, bloqueo de credenciales y revocación de tokens.
- Logging de auditoría con IP hash y user-agent hash.
- Despliegue en Docker con soporte de GPU (CUDA).

Los secrets, IPs internas y credenciales han sido removidos para mantener la seguridad del sistema productivo.

---

## Licencia

Proyecto privado — código mostrado con fines de portafolio.

---

**Autor:** [Jorge Armando Vicente Martínez](https://github.com/JAVM11) · Built with ☕ and Python
