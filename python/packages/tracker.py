import math
from datetime import datetime


def now_iso():
    return datetime.now().isoformat()


def distance_pixels(p1, p2):
    """
    Calcule la distance entre deux points pixels.
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx * dx + dy * dy)


class SimpleObjectTracker:
    """
    Tracker simple basé sur la distance entre les centres des objets.

    Rôle :
        - Donner une ID unique à chaque objet détecté.
        - Garder la même ID si l'objet est retrouvé dans les frames suivantes.
        - Conserver l'objet quelques frames même s'il disparaît.
        - Réestimer sa position pendant une courte disparition.

    Limite :
        Ce tracker est simple.
        Il ne reconnaît pas visuellement l'objet.
        Il se base seulement sur sa position dans l'image.
    """

    def __init__(self, max_distance=80, max_missing_frames=30):
        """
        Args:
            max_distance (float):
                Distance maximale en pixels pour considérer qu'une détection
                correspond à un objet déjà suivi.

            max_missing_frames (int):
                Nombre maximum de frames pendant lesquelles un objet peut
                disparaître avant d'être supprimé.
        """

        self.next_id = 1
        self.tracks = {}

        self.max_distance = max_distance
        self.max_missing_frames = max_missing_frames

    def update(self, detections):
        """
        Met à jour le tracker avec les détections YOLO.

        Args:
            detections (list):
                Liste sous forme :
                [
                    {
                        "center": (cx, cy),
                        "class_id": class_id,
                        "confidence": conf
                    }
                ]

        Returns:
            list:
                Liste des objets suivis avec leur track_id.
        """

        assigned_tracks = set()
        assigned_detections = set()

        # --------------------------------------------------
        # 1. Association des nouvelles détections aux tracks existants
        # --------------------------------------------------
        for det_index, det in enumerate(detections):
            det_center = det["center"]

            best_track_id = None
            best_distance = None

            for track_id, track in self.tracks.items():
                if track_id in assigned_tracks:
                    continue

                # On évite d'associer deux classes différentes.
                if track["class_id"] != det["class_id"]:
                    continue

                track_center = track["center"]
                dist = distance_pixels(det_center, track_center)

                if dist <= self.max_distance:
                    if best_distance is None or dist < best_distance:
                        best_distance = dist
                        best_track_id = track_id

            if best_track_id is not None:
                track = self.tracks[best_track_id]

                old_cx, old_cy = track["center"]
                new_cx, new_cy = det_center

                # Vitesse approximative en pixels/frame.
                vx = new_cx - old_cx
                vy = new_cy - old_cy

                track["center"] = det_center
                track["velocity_px"] = (vx, vy)
                track["confidence"] = det["confidence"]
                track["missing_frames"] = 0
                track["last_seen"] = now_iso()
                track["estimated"] = False

                assigned_tracks.add(best_track_id)
                assigned_detections.add(det_index)

        # --------------------------------------------------
        # 2. Création d'une nouvelle ID pour les détections non associées
        # --------------------------------------------------
        for det_index, det in enumerate(detections):
            if det_index in assigned_detections:
                continue

            track_id = self.next_id
            self.next_id += 1

            self.tracks[track_id] = {
                "track_id": track_id,
                "center": det["center"],
                "velocity_px": (0, 0),
                "class_id": det["class_id"],
                "confidence": det["confidence"],
                "missing_frames": 0,
                "first_seen": now_iso(),
                "last_seen": now_iso(),
                "estimated": False
            }

        # --------------------------------------------------
        # 3. Réestimation des objets non vus dans cette frame
        # --------------------------------------------------
        tracks_to_delete = []

        for track_id, track in self.tracks.items():
            if track_id in assigned_tracks:
                continue

            # Si le track n'a pas été mis à jour,
            # on considère que l'objet est temporairement perdu.
            track["missing_frames"] += 1

            if track["missing_frames"] > 0:
                cx, cy = track["center"]
                vx, vy = track["velocity_px"]

                # Réestimation simple :
                # nouvelle position = ancienne position + vitesse connue.
                track["center"] = (cx + vx, cy + vy)
                track["estimated"] = True

            # Si l'objet est perdu trop longtemps, on supprime son ID.
            if track["missing_frames"] > self.max_missing_frames:
                tracks_to_delete.append(track_id)

        for track_id in tracks_to_delete:
            del self.tracks[track_id]

        return list(self.tracks.values())