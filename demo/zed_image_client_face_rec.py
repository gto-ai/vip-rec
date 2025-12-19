import cv2
import zmq
import time
import numpy as np
from loguru import logger
import threading

from util.face_helper import FaceRec
from util.g1_helper import G1


def greet(robot, name):
    if name == 'UNKNOWN':
        robot.say("Hello, welcome to the airshow!")
    else:
        robot.say(f"Hello, {name}, welcome to the airshow!")
    robot.wave_hand()


class ImageClient:
    def __init__(self, **kwargs):
        self.running = True
        self.image_show = kwargs.get('image_show', False)
        self.server_address = kwargs.get('server_address', "192.168.123.123")
        self.port = kwargs.get('port', 5555)

        self.socket = None
        self.context = None

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

    def launch_zmq_subscriber(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(f"tcp://{self.server_address}:{self.port}")
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")

        logger.info("[ImageClient] Started, waiting for images...")

    def receive_process(self):
        self.launch_zmq_subscriber()
        face_rec = FaceRec()
        robot = G1()
        last_rec_time = 0.0
        unknown_cnt = 0

        while self.running:
            message = self.socket.recv()

            # Decode JPEG
            np_img = np.frombuffer(message, dtype=np.uint8)
            frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
            if frame is None:
                logger.error("[ImageClient] Failed to decode image")
                continue

            left_img, right_img = self.get_stereo_images(frame)

            current_time = time.time()
            if current_time - last_rec_time >= 1.0:
                left_img, name = face_rec.recognize(left_img)
                last_rec_time = current_time
                if name is not None and robot.state == 'idle':
                    if name == "UNKNOWN":
                        unknown_cnt += 1
                        if unknown_cnt < 3:
                            continue

                    threading.Thread(
                        target=greet,
                        args=(robot, name),
                        daemon=True
                    ).start()

                    unknown_cnt = 0

                # display
                if self.image_show:
                    cv2.imshow("Face Recognition", left_img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.running = False
            else:
                pass


if __name__ == "__main__":
    client = ImageClient(
        image_show=True,
        server_address="192.168.123.164",
    )
    client.receive_process()
