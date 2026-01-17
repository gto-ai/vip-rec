import cv2
import zmq
import time
import numpy as np
from loguru import logger
import json
from util.face_helper import FaceRec
from util.redis_helper import Redis


class FaceUtil:
    @classmethod
    def center_crop(cls, frame, ratio=0.6):
        height, width = frame.shape[:2]

        crop_w = int(width * ratio)
        crop_h = int(height * ratio)

        x1 = (width - crop_w) // 2
        y1 = (height - crop_h) // 2
        x2 = x1 + crop_w
        y2 = y1 + crop_h

        crop = frame[y1:y2, x1:x2]

        return crop

    @classmethod
    def get_center_face(cls, results, height, width):
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

    @classmethod
    def draw_face(cls, frame, r, name):
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


class CameraAgent:
    def __init__(self, **kwargs):
        self.running = True
        self.image_show = kwargs.get('image_show', False)
        self.camera_ip = kwargs.get('camera_ip', "192.168.123.164")

        self.context = zmq.Context()
        self.camera_sub = self.context.socket(zmq.SUB)
        self.camera_sub.connect(f"tcp://{self.camera_ip}:5555")
        self.camera_sub.setsockopt_string(zmq.SUBSCRIBE, "")

        self.audio_ip = kwargs.get('camera_ip', "127.0.0.1")
        self.audio_pub = self.context.socket(zmq.PUB)
        self.audio_pub.bind(f"tcp://{self.audio_ip}:5556")

    def get_stereo_images(self, frame):
        h, w = frame.shape[:2]
        half_w = w // 2

        left_img = frame[:, :half_w]
        right_img = frame[:, half_w:]

        return left_img, right_img

    def get_right_image(self, frame):
        pass

    def close(self):
        self.socket.close()
        self.context.term()
        if self.image_show:
            cv2.destroyAllWindows()

        logger.info("[ImageClient] Closed")

    def run(self):
        logger.info('Camera agent is running.')

        face_rec = FaceRec()
        last_rec_time = 0.0
        unknown_cnt = 0

        while self.running:
            message = self.camera_sub.recv()

            # Decode JPEG
            np_img = np.frombuffer(message, dtype=np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if frame is None:
                logger.error("[ImageClient] Failed to decode image")
                continue

            left_img, right_img = self.get_stereo_images(frame)
            left_img = FaceUtil.center_crop(left_img, ratio=0.6)

            current_time = time.time()
            if current_time - last_rec_time >= 1.0:
                left_img, name = face_rec.recognize(left_img)
                last_rec_time = current_time
                logger.warning(f"recognize {name}")

                audio_status = Redis.get('audio_status')
                if name is not None and audio_status == 'idle':

                    if name == "UNKNOWN":
                        unknown_cnt += 1
                        if unknown_cnt < 3:
                            continue

                    vip_info = Redis.get('vip')
                    if vip_info['status'] == 'on' and vip_info['mode'] == 'manual':
                        logger.info("Ignore all the actions")
                    else:
                        # do greeting
                        params = {
                            "name": name,
                            "article": "article_1"
                        }
                        logger.info("Trigger action")
                        Redis.set('audio_status', 'busy')
                        self.audio_pub.send_string(json.dumps(params))

                    unknown_cnt = 0

                # display
                if self.image_show:
                    cv2.imshow("Face Recognition", left_img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.running = False
            else:
                pass


if __name__ == "__main__":
    client = CameraAgent(
        image_show=True,
        server_address="192.168.123.164",
    )
    client.run()
