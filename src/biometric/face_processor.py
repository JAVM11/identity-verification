"""
Procesamiento facial: landmarks con MediaPipe y codificación 128-D
con face_recognition. Extraído del motor productivo IDVE.
"""
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import cv2
import numpy as np

# Nota: en el demo estas importaciones se hacen bajo demanda
# para no romper si no están instaladas las libs pesadas.
try:
    import mediapipe as mp
    import face_recognition
    MP_AVAILABLE = True
except Exception:
    MP_AVAILABLE = False


class FaceProcessor:
    """
    Encapsula la detección de landmarks (MediaPipe FaceMesh)
    y la generación de embeddings faciales (face_recognition).
    """

    def __init__(self):
        self.face_mesh = None
        if MP_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=False,
            )

    def obtener_landmarks(self, imagen: np.ndarray):
        """
        Retorna un array NumPy con los 468 landmarks faciales
        en coordenadas de píxeles, o None si no hay rostro.
        """
        if self.face_mesh is None or imagen is None or imagen.size == 0:
            return None

        h, w = imagen.shape[:2]
        resultados = self.face_mesh.process(
            cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        )

        if not resultados.multi_face_landmarks:
            return None

        landmarks = resultados.multi_face_landmarks[0].landmark
        puntos = np.array(
            [(lm.x * w, lm.y * h) for lm in landmarks], dtype=np.int32
        )
        return puntos

    def obtener_encoding(self, imagen_bgr: np.ndarray):
        """
        Genera el embedding facial 128-D usando face_recognition.
        Retorna None si no detecta rostro.
        """
        if not MP_AVAILABLE or imagen_bgr is None or imagen_bgr.size == 0:
            return None

        rgb = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb)
        return encodings[0] if encodings else None

    def comparar(self, encoding_a, encoding_b, tolerance: float = 0.6):
        """
        Compara dos embeddings. Retorna (match: bool, distance: float).
        """
        if encoding_a is None or encoding_b is None:
            return False, None

        dist = float(np.linalg.norm(encoding_a - encoding_b))
        match = bool(face_recognition.compare_faces(
            [encoding_a], encoding_b, tolerance=tolerance
        )[0])
        return match, dist


def recortar_rostro_desde_rectangulo(
    imagen: np.ndarray, rect: tuple, padding_ratio: float = 0.25
):
    """
    Recorta un rostro dado un rectángulo (x, y, w, h) de OpenCV
    con padding proporcional.
    """
    if imagen is None or imagen.size == 0:
        return None

    x, y, w, h = rect
    pad = int(w * padding_ratio)

    x1 = max(x - pad, 0)
    y1 = max(y - pad, 0)
    x2 = min(x + w + pad, imagen.shape[1])
    y2 = min(y + h + pad, imagen.shape[0])

    recorte = imagen[y1:y2, x1:x2]
    return recorte if recorte.size > 0 else None
