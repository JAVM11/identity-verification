# Códigos de Respuesta Lógicos

El sistema utiliza códigos propios dentro del campo `codigo` para indicar el resultado del proceso de verificación, independientemente del status HTTP.

| Código | Descripción | Acción Frontend |
|--------|-------------|-----------------|
| `200` | Proceso correcto. Misma persona y datos completos. | Continuar flujo. |
| `201` | Misma persona, pero con datos OCR incompletos o advertencias. | Mostrar advertencia; permitir continuar con revisión manual. |
| `202` | Misma persona, pero no se pudo leer QR de vigencia. | Solicitar segunda verificación o revisión manual. |
| `203` | **No es la misma persona.** | Rechazar verificación. |
| `204` | No se pudo detectar rostro, landmarks o codificación facial. | Solicitar nueva foto con mejor iluminación/posición. |
| `205` | No existe la imagen de rostro en el servidor. | Reintentar upload de rostro previo. |
| `206` | No se pudo leer INE frontal. | Solicitar nueva foto del frontal. |
| `207` | No se pudo leer INE reverso. | Solicitar nueva foto del reverso. |
| `400` | Error en la petición o archivos inválidos. | Corregir request. |
| `500` | Error interno durante el procesamiento. | Reintentar más tarde; alertar a soporte. |

## Estructura de error estándar

```json
{
  "code": "FACE_MISMATCH",
  "message": "No es la misma persona",
  "source": "faceComparison",
  "detail": null
}
```
