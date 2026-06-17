import cv2
import numpy as np
import onnxruntime as ort


# Taille d'entrée attendue par le modèle ONNX.
# L'image sera redimensionnée en 1024x1024 avant l'inférence.
INPUT_SIZE = 1024

# Seuil de confiance minimal pour garder une détection.
CONF_THRESHOLD = 0.6


def openFlowRTSP(url):
    """
    Ouvre un flux vidéo RTSP ou une vidéo locale.

    Args:
        url (str): URL du flux vidéo ou chemin vers une vidéo.

    Returns:
        cv2.VideoCapture | None:
            Objet de lecture vidéo si l'ouverture réussit,
            sinon None.
    """

    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("Erreur : impossible d'ouvrir le flux vidéo")
        return None

    return cap


def closeFlowRTSP(cap):
    """
    Ferme proprement le flux vidéo.

    Args:
        cap: Objet OpenCV VideoCapture.

    Returns:
        None
    """

    if cap is not None:
        cap.release()


def readFrame(cap):
    """
    Lit une image depuis le flux vidéo.

    Args:
        cap: Objet OpenCV VideoCapture.

    Returns:
        tuple:
            frame : image lue.
            ret   : True si l'image est correctement lue, False sinon.
    """

    if cap is None:
        return None, False

    ret, frame = cap.read()

    return frame, ret


def loadModel(model_path):
    """
    Charge le modèle ONNX avec ONNX Runtime.

    Args:
        model_path (str): Chemin vers le fichier .onnx.

    Returns:
        tuple:
            session    : session ONNX Runtime.
            input_name : nom de l'entrée du modèle.
    """

    session = ort.InferenceSession(
        model_path,
        providers=["CPUExecutionProvider"]
    )

    input_name = session.get_inputs()[0].name

    print("Model loaded")
    print("Input name:", input_name)

    return session, input_name


def preprocess(frame):
    """
    Prépare une image avant de l'envoyer au modèle ONNX.

    Étapes :
        1. Redimensionnement en INPUT_SIZE x INPUT_SIZE.
        2. Conversion BGR vers RGB.
        3. Normalisation entre 0 et 1.
        4. Passage du format HWC vers CHW.
        5. Ajout d'une dimension batch.

    Args:
        frame: Image OpenCV au format BGR.

    Returns:
        np.ndarray: Tensor prêt pour le modèle ONNX.
    """

    img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = img.astype(np.float32) / 255.0
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    return img


def modelResults(session, input_name, input_tensor):
    """
    Exécute le modèle ONNX sur une image prétraitée.

    Args:
        session: Session ONNX Runtime.
        input_name (str): Nom de l'entrée du modèle.
        input_tensor (np.ndarray): Image prétraitée.

    Returns:
        np.ndarray: Sortie brute du modèle.
    """

    outputs = session.run(None, {input_name: input_tensor})

    return outputs[0]


def detectionsToBoxes(detections, original_w, original_h):
    """
    Transforme les sorties du modèle en bounding boxes exploitables.

    Le modèle donne généralement :
        x_center, y_center, width, height, scores_classes...

    Cette fonction :
        - récupère la classe la plus probable ;
        - filtre avec CONF_THRESHOLD ;
        - convertit les coordonnées vers la taille originale de l'image ;
        - limite les coordonnées pour ne pas sortir de l'image.

    Args:
        detections (np.ndarray): Sortie brute du modèle.
        original_w (int): Largeur originale de l'image.
        original_h (int): Hauteur originale de l'image.

    Returns:
        list: Liste des boxes sous forme :
              (x1, y1, x2, y2, confidence, class_id)
    """

    boxes = []

    detections = np.squeeze(detections)

    # Si une seule détection est présente, on garde une structure 2D.
    if len(detections.shape) == 1:
        detections = np.expand_dims(detections, axis=0)

    # Certains modèles sortent les données transposées.
    # Cette condition corrige ce cas.
    if len(detections.shape) == 2 and detections.shape[0] < detections.shape[1]:
        detections = detections.T

    for det in detections:
        det = np.array(det).flatten()

        # Une détection doit contenir au minimum :
        # x, y, width, height, score_classe_1, score_classe_2...
        if len(det) < 6:
            continue

        x_center = float(det[0])
        y_center = float(det[1])
        width = float(det[2])
        height = float(det[3])

        class_scores = det[4:]
        class_id = int(np.argmax(class_scores))
        conf = float(class_scores[class_id])

        # On ignore les détections peu fiables.
        if conf < CONF_THRESHOLD:
            continue

        # Conversion centre + taille vers coins x1, y1, x2, y2.
        x1 = int((x_center - width / 2) * original_w / INPUT_SIZE)
        y1 = int((y_center - height / 2) * original_h / INPUT_SIZE)
        x2 = int((x_center + width / 2) * original_w / INPUT_SIZE)
        y2 = int((y_center + height / 2) * original_h / INPUT_SIZE)

        # Sécurité : on empêche les coordonnées de sortir de l'image.
        x1 = max(0, min(x1, original_w - 1))
        x2 = max(0, min(x2, original_w - 1))
        y1 = max(0, min(y1, original_h - 1))
        y2 = max(0, min(y2, original_h - 1))

        boxes.append((x1, y1, x2, y2, conf, class_id))

    return boxes


def drawBoxes(frame, boxes):
    """
    Dessine les bounding boxes sur l'image et récupère leurs centres.

    Args:
        frame: Image OpenCV.
        boxes (list): Liste de bounding boxes.

    Returns:
        tuple:
            frame   : image annotée.
            centers : liste des centres sous forme :
                      (cx, cy, class_id, confidence)
    """

    centers = []

    for x1, y1, x2, y2, conf, class_id in boxes:
        # Centre de la bounding box.
        cx = int((x1 + x2) / 2)
        cy = int((y1 + y2) / 2)

        centers.append((cx, cy, class_id, conf))

        # Dessin de la boîte.
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Dessin du centre.
        cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        # Texte affiché sur l'image.
        cv2.putText(
            frame,
            f"id:{class_id} {conf:.2f} C({cx},{cy})",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

    return frame, centers


def createVideoWriter(output_path, cap, first_frame):
    """
    Crée un fichier vidéo de sortie.

    Args:
        output_path (str): Chemin du fichier vidéo de sortie.
        cap: Flux vidéo OpenCV.
        first_frame: Première image lue.

    Returns:
        cv2.VideoWriter | None:
            Objet d'écriture vidéo, ou None si erreur.
    """

    h, w = first_frame.shape[:2]

    fps = cap.get(cv2.CAP_PROP_FPS)

    # Certains flux RTSP retournent un FPS invalide.
    # On force donc une valeur raisonnable.
    if fps <= 0 or fps > 60:
        fps = 20

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    writer = cv2.VideoWriter(
        output_path,
        fourcc,
        fps,
        (w, h)
    )

    if not writer.isOpened():
        print("Erreur : impossible de créer la vidéo")
        return None

    print(f"Vidéo de sortie créée : {output_path}")
    print(f"Taille : {w}x{h}, FPS : {fps}")

    return writer