import cv2
import re
from deepface import DeepFace
from pathlib import Path
from loguru import logger
from config import DATA


class FaceRec:
    def __init__(self, **kwargs):
        self.db_path = kwargs.get('db_path', str(Path(DATA, "vip_images")))
        self.THRESHOLD = kwargs.get('THRESHOLD', 60)

    def center_crop(self, frame, ratio=0.6):
        height, width = frame.shape[:2]

        crop_w = int(width * ratio)
        crop_h = int(height * ratio)

        x1 = (width - crop_w) // 2
        y1 = (height - crop_h) // 2
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        crop = frame[y1:y2, x1:x2]

        return crop

    def get_center_face(self, results, height, width):
        x_center, y_center = width // 2, height // 2

        min_dist = 99999
        min_idx = -1
        for idx, df in enumerate(results):
            r = df.iloc[0]
            x, y, w, h = int(r["source_x"]), int(r["source_y"]), int(r["source_w"]), int(r["source_h"])
            xc, yc = x + w // 2, y + h // 2
            dist = (x_center - xc) * (x_center - xc) + (y_center - yc) * (y_center - yc)
            if dist < min_dist:
                min_dist = dist
                min_idx = idx

        return min_idx

    def draw_face(self, frame, r, name):
        x, y, w, h = int(r["source_x"]), int(r["source_y"]), int(r["source_w"]), int(r["source_h"])

        if name == 'UNKNOWN':
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

            cv2.putText(
                frame, name,
                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 0, 255), 2
            )
        else:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            cv2.putText(
                frame, name,
                (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (0, 255, 0), 2
            )

        return frame

    def recognize(self, frame):
        results = DeepFace.find(
            img_path=frame,
            db_path=self.db_path,
            model_name="ArcFace",
            detector_backend="retinaface",
            enforce_detection=False
        )

        logger.info(results)

        if len(results) > 0 and len(results[0]) > 0:  # detected

            logger.debug(f"Detected no. of faces: {len(results)}")
            print(results)

            height, width = frame.shape[:2]
            min_idx = self.get_center_face(results, height, width)
            logger.info(f"min_idx: {min_idx} height: {height} width: {width}")

            df = results[min_idx]
            row = df.iloc[0]
            logger.info(f"Row: {row}")

            if row['confidence'] <= self.THRESHOLD:  # detected and face not in DB
                name = 'UNKNOWN'
            else:  # detected and face in DB
                x, y, w, h = int(row["source_x"]), int(row["source_y"]), int(row["source_w"]), int(row["source_h"])
                logger.info(f"x: {x} y: {y} w: {w} h: {h}, height: {height}, width: {width}")
                if w * h >= 0.8 * width * height:
                    return frame, None

                if w * h <= 0.1 * width * height:
                    return frame, None

                identity = Path(row['identity']).stem

                name = identity
                name = re.sub(r"\s*\d+$", "", name)

                logger.info(f"Identity: {identity} {name}")

            frame = self.draw_face(frame, row, name)

            logger.info(f"Confidence: {row['confidence']}, Distance: {row['distance']}")

            return frame, name

        else:  # no face detected
            return frame, None

    def run(self, **kwargs):
        device_id = kwargs.get('device_id', '/dev/video0')
        cap = cv2.VideoCapture(device_id)

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            try:
                frame, name = self.recognize(frame)

            except Exception as e:
                logger.error(f"Error: {e}")

            cv2.imshow("Face Recognition", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        cap.release()
        cv2.destroyAllWindows()


def main():
    face_rec = FaceRec()
    face_rec.run()


if __name__ == '__main__':
    main()
