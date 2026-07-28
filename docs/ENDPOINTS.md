# Documentación de Endpoints — IDVE Showcase

> Versión simplificada para demostración. Los endpoints productivos incluyen validación JWT en cada petición, rate limiting y auditoría de requests.

---

## Healthcheck

### `GET /`

Valida que el servicio está activo.

**Ejemplo:**
```bash
curl -X GET http://localhost:5000/
```

**Respuesta:**
```json
{
  "status": "IDVE Showcase activo",
  "version": "1.0.0-demo"
}
```

---

## Autenticación

### `POST /auth/token`

Genera un access token JWT de demostración.

**Body:**
```json
{
  "tenant_code": "DEMO",
  "environment": "sandbox",
  "username": "demo@idve.mx"
}
```

**Respuesta:**
```json
{
  "codigo": 200,
  "status": "FINISH",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

### `GET /auth/validate`

Valida un token vía header `Authorization: Bearer <token>`.

**Ejemplo:**
```bash
curl -X GET http://localhost:5000/auth/validate \
  -H "Authorization: Bearer <token>"
```

---

## Verificación Biométrica

### `POST /api/procesarRostros`

Comparación facial 1:1 directa.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `rostro1` | File | Primera imagen |
| `rostro2` | File | Segunda imagen |

**Ejemplo:**
```bash
curl -X POST http://localhost:5000/api/procesarRostros \
  -F "rostro1=@/ruta/rostro_a.jpg" \
  -F "rostro2=@/ruta/rostro_b.jpg"
```

---

### `POST /api/procesarIneJuntoRostro`

Pipeline completo: INE frontal + reverso + rostro real.

**Content-Type:** `multipart/form-data`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `INEFrontal` | File | Imagen frontal de la credencial |
| `INEReverso` | File | Imagen reverso de la credencial |
| `Rostro` | String | Nombre/ruta del rostro almacenado |

**Respuesta estándar:**
```json
{
  "codigo": 200,
  "respuestaverifica": {
    "status": "FINISH",
    "result": 100,
    "errors": [],
    "identity": {
      "fullName": "...",
      "curp": "...",
      "cic": "...",
      "identificador_ciudadano": "...",
      "urlVigencia": "..."
    },
    "dataOcr": {
      "type": "ID",
      "issue_country": "MEX",
      "doc_number": "...",
      ...
    },
    "faceComparison": {
      "result": true,
      "similarity": 0.3842
    }
  }
}
```

---

## Utilidades (Demo)

### `POST /demo/mrz-parse`

Parsea 3 líneas MRZ sin necesidad de OCR.

**Body:**
```json
{
  "lineas": [
    "IDMEX1234567890<<<<<<<<<<<<<<<",
    "0000000H0000000MEX<<<<<<<<<<<0",
    "APELLIDO<<NOMBRE<NOMBRE2<<<<<"
  ]
}
```

---

### `POST /demo/curp-reconstruct`

Reconstruye CURP desde candidatos OCR + máscara MRZ.

**Body:**
```json
{
  "textos_frontales": ["CURP: GARJ041121HDFLRN09"],
  "datos_extraidos": {
    "dataOcr": {
      "last_name": "GARCIA",
      "last_name2": "LOPEZ",
      "first_name": "JUAN",
      "date_birth": "2004-11-21",
      "sex": "M"
    }
  }
}
```
