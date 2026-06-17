import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = BASE_DIR.parent / "packages"

sys.path.append(str(PACKAGES_DIR))

from treatVideo import *

def main(model_path,source):
    session, input_name = loadModel(model_path)

    cap = openFlowRTSP(source)

    if cap is None:
        return

    first_frame, ret = readFrame(cap)

    if not ret:
        print("Impossible de lire la première frame")
        closeFlowRTSP(cap)
        return

    # out = createVideoWriter(OUTPUT_PATH, cap, first_frame)

    # if out is None:
    #     closeFlowRTSP(cap)
    #     return

    try:
        while True:
            frame, ret = readFrame(cap)

            if not ret:
                print("End of stream")
                break

            original_h, original_w = frame.shape[:2]

            input_tensor = preprocess(frame)

            detections = modelResults(session, input_name, input_tensor)

            boxes = detectionsToBoxes(
                detections,
                original_w,
                original_h
            )

            frame_with_boxes, centers = drawBoxes(frame, boxes)

            # out.write(frame_with_boxes)

    except KeyboardInterrupt:
        print("Arrêt demandé avec CTRL+C")

    finally:
        # out.release()
        closeFlowRTSP(cap)
        # print(f"Vidéo sauvegardée: {OUTPUT_PATH}")


source = 0

model_path = "/home/ahmed/Bureau/projet_propre/model/DOTAlast.onnx"

# TreatVideo_main(source,model_path)

    


if __name__ == "__main__":
    main(model_path,source)