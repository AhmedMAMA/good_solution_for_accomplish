import time
import sys
import os

sys.path.append(os.path.abspath("../packages"))

from dronePosition import (
    connect_mavlink,
    create_initial_state,
    update_state
)

from treatVideo import (
    openFlowRTSP,
    closeFlowRTSP,
    readFrame,
    loadModel,
    preprocess,
    modelResults,
    detectionsToBoxes,
    drawBoxes,
    createVideoWriter
)

from objectPosition import estimatePosition

from tracker import SimpleObjectTracker


MODEL_PATH = "/home/ahmed/Documents/next/nigma_conseil/script_prorpre/models/TacticalAI_trt_raw.onnx"
VIDEO_SOURCE = "rtsp://192.168.144.25:8554/main.264"
OUTPUT_VIDEO = "../res/output_detection.mp4"

FOV_X = 70
FOV_Y = 43


def get_best_heading(position, orientation):
    """
    Choisit la meilleure orientation disponible du drone.
    """

    if orientation is not None:
        yaw = orientation.get("yaw_deg")

        if yaw is not None:
            return yaw

    if position is not None:
        heading = position.get("heading_deg")

        if heading is not None:
            return heading

    return 0


def main():
    """
    Programme principal :

        1. Lit MAVLink.
        2. Lit la vidéo.
        3. Détecte les objets avec YOLO/ONNX.
        4. Donne une ID à chaque objet.
        5. Garde l'ID si l'objet disparaît peu de temps.
        6. Réestime la position de l'objet perdu.
        7. Calcule la position relative/GPS de chaque objet.
    """

    session, input_name = loadModel(MODEL_PATH)

    cap = openFlowRTSP(VIDEO_SOURCE)

    if cap is None:
        return

    first_frame, ret = readFrame(cap)

    if not ret:
        print("Impossible de lire la première image")
        closeFlowRTSP(cap)
        return

    writer = createVideoWriter(OUTPUT_VIDEO, cap, first_frame)

    master = connect_mavlink()
    drone_state = create_initial_state()

    tracker = SimpleObjectTracker(
        max_distance=100,
        max_missing_frames=30
    )

    wanted_messages = {
        "HEARTBEAT",
        "GLOBAL_POSITION_INT",
        "GPS_RAW_INT",
        "ATTITUDE",
        "VFR_HUD",
        "SYS_STATUS"
    }

    try:
        while True:
            # --------------------------------------------------
            # 1. Lecture MAVLink
            # --------------------------------------------------
            msg = master.recv_match(blocking=False)

            while msg is not None:
                msg_type = msg.get_type()

                if msg_type != "BAD_DATA" and msg_type in wanted_messages:
                    drone_state = update_state(drone_state, msg)

                msg = master.recv_match(blocking=False)

            # --------------------------------------------------
            # 2. Lecture vidéo
            # --------------------------------------------------
            frame, ret = readFrame(cap)

            if not ret:
                print("Image non lue")
                time.sleep(0.1)
                continue

            h, w = frame.shape[:2]

            # --------------------------------------------------
            # 3. Détection ONNX
            # --------------------------------------------------
            input_tensor = preprocess(frame)

            detections = modelResults(
                session,
                input_name,
                input_tensor
            )

            boxes = detectionsToBoxes(
                detections,
                w,
                h
            )

            frame, centers = drawBoxes(
                frame,
                boxes
            )

            # --------------------------------------------------
            # 4. Conversion centers YOLO vers format tracker
            # --------------------------------------------------
            tracker_inputs = []

            for cx, cy, class_id, conf in centers:
                tracker_inputs.append({
                    "center": (cx, cy),
                    "class_id": class_id,
                    "confidence": conf
                })

            # --------------------------------------------------
            # 5. Mise à jour du tracker
            # --------------------------------------------------
            tracked_objects = tracker.update(tracker_inputs)

            # --------------------------------------------------
            # 6. Récupération télémétrie
            # --------------------------------------------------
            position = drone_state.get("position")
            orientation = drone_state.get("orientation")

            objects_positions = []

            if position is not None:
                altitude = position.get("relative_altitude_m")
                lat = position.get("latitude")
                lon = position.get("longitude")
                heading = get_best_heading(position, orientation)

                if altitude is not None:
                    for track in tracked_objects:
                        cx, cy = track["center"]

                        obj_position = estimatePosition(
                            x_center_box=cx,
                            y_center_box=cy,
                            frame_width=w,
                            frame_height=h,
                            fov_x_deg=FOV_X,
                            fov_y_deg=FOV_Y,
                            alt=altitude,
                            lat=lat,
                            lon=lon,
                            heading_deg=heading
                        )

                        obj_position["track_id"] = track["track_id"]
                        obj_position["class_id"] = track["class_id"]
                        obj_position["confidence"] = track["confidence"]
                        obj_position["missing_frames"] = track["missing_frames"]
                        obj_position["estimated"] = track["estimated"]
                        obj_position["last_seen"] = track["last_seen"]

                        objects_positions.append(obj_position)

            # --------------------------------------------------
            # 7. Affichage terminal
            # --------------------------------------------------
            if objects_positions:
                print("Objets suivis :")

                for obj in objects_positions:
                    print(
                        "ID:",
                        obj["track_id"],
                        "| class:",
                        obj["class_id"],
                        "| estimated:",
                        obj["estimated"],
                        "| missing:",
                        obj["missing_frames"],
                        "| relative:",
                        obj["relative_position_m"],
                        "| gps:",
                        obj["gps"]
                    )

            # --------------------------------------------------
            # 8. Écriture vidéo
            # --------------------------------------------------
            if writer is not None:
                writer.write(frame)

    except KeyboardInterrupt:
        print("\nArrêt utilisateur")

    except Exception as e:
        print("Erreur :", e)

    finally:
        closeFlowRTSP(cap)

        if writer is not None:
            writer.release()

        print("Programme terminé")


if __name__ == "__main__":
    main()