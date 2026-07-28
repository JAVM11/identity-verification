# Arquitectura Técnica — IDVE

## Visión general

IDVE es un backend de inferencia para verificación de identidad. Opera como un servicio stateless (salvo sesiones de token) que recibe imágenes, ejecuta modelos de visión y OCR, y devuelve una decisión estructurada.

## Diagrama de flujo

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Cliente   │────▶│  Flask API       │────▶│  Validación JWT │
│  (Frontend) │     │  (IDVE Backend)  │     │  + Scopes       │
└─────────────┘     └──────────────────┘     └─────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────────┐
        │  1. Recepción de archivos (multipart)       │
        │  2. Guardado temporal en disco              │
        │  3. Carga con OpenCV                        │
        └─────────────────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌────────────┐   ┌────────────┐   ┌──────────────┐
    │ INE Frontal│   │ INE Reverso│   │ Rostro Real  │
    │            │   │            │   │ (pre-cargado)│
    └─────┬──────┘   └─────┬──────┘   └──────┬───────┘
          │                │                   │
          ▼                ▼                   ▼
    ┌──────────┐    ┌──────────┐      ┌──────────────┐
    │ OCR      │    │ QR + MRZ │      │ Face Encoding│
    │ Paddle   │    │ QReader  │      │ 128-D        │
    └─────┬────┘    └─────┬────┘      └──────┬───────┘
          │               │                    │
          └───────────────┼────────────────────┘
                          ▼
              ┌───────────────────────┐
              │ Comparación Facial 1:1│
              │ face_recognition      │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │ Extracción estructurada│
              │ - Nombre completo      │
              │ - CURP (reconstruido)  │
              │ - CIC / identificador  │
              │ - URL de vigencia (QR) │
              └───────────┬───────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │  Respuesta JSON       │
              │  con códigos lógicos  │
              └───────────────────────┘
```

## Componentes clave

### Biometría (`src/biometric/`)
- **MediaPipe FaceMesh**: 468 landmarks para validar que hay un rostro humano real (anti-spoofing básico).
- **face_recognition**: Encoding 128-D basado en dlib. Comparación euclidiana.
- **OpenCV Haar Cascade**: Detección del rostro en la INE para recorte antes del encoding.

### OCR (`src/ocr/`)
- **PaddleOCR**: Motor principal con clasificación de ángulo y modelo en español.
- **QReader**: Lectura de códigos QR en el reverso de la credencial.
- **Parser MRZ**: Implementación propia del estándar ICAO 9303 para TD1 (3 líneas × 30 caracteres).
- **Reconstructor CURP**: Algoritmo heurístico que cruza MRZ + OCR frontal para obtener la CURP con alta confianza, incluso cuando el OCR es ruidoso.

### Auth (`src/auth/`)
- **JWT**: Tokens con `jti` único, control de expiración y revocación en base de datos.
- **Multi-tenant**: Cada usuario pertenece a un `tenant` con scopes independientes por ambiente (`sandbox` vs `production`).
- **Hashing**: Credenciales con SHA-256 (compatibilidad) y preparado para Argon2id.

## Decisiones de diseño

1. **Carga de modelos en `__init__`**: Los modelos de OCR y face mesh se cargan una sola vez al iniciar el contenedor. Esto evita latencias de >10s por request.
2. **Supresión de logs de librerías**: PaddleOCR y TensorFlow son muy verbosos. Se redirige stderr/stdout a `/dev/null` durante importación para mantener logs limpios.
3. **Respuestas estandarizadas**: Todos los endpoints devuelven el mismo envelope (`codigo`, `respuestaverifica`, `errors[]`) para que el frontend no tenga que manejar formatos mixtos.
4. **Códigos lógicos propios**: En lugar de depender únicamente de HTTP status, el sistema expone códigos de negocio (200, 201, 203, 204...) que el frontend usa para decidir el siguiente paso del flujo de verificación.

## Escalabilidad (productivo)

- **MySQL Connection Pool**: Pool de 5 conexiones por worker.
- **GPU**: PaddlePaddle con CUDA para OCR en milisegundos.
- **Docker**: Imagen `capromdev/autenticacionback:v1.3` con todas las libs compiladas.
- **Stateless**: Ideal para escalar horizontalmente; la única dependencia stateful es la sesión de token en MySQL.
