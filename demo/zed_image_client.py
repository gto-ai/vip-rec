import cv2
import zmq
import numpy as np
from loguru import logger


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

        try:
            while self.running:
                message = self.socket.recv()

                # Decode JPEG
                np_img = np.frombuffer(message, dtype=np.uint8)
                frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
                if frame is None:
                    logger.error("[ImageClient] Failed to decode image")
                    continue

                left_img, right_img = self.get_stereo_images(frame)

                # display
                if self.image_show:
                    cv2.imshow("TV Camera Stream", left_img)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        self.running = False

        except KeyboardInterrupt:
            print("[ImageClient] Interrupted by user")
        except Exception as e:
            print(f"[ImageClient] Error: {e}")
        finally:
            self.close()


if __name__ == "__main__":
    client = ImageClient(
        image_show=True,
        server_address="192.168.123.164",
    )
    client.receive_process()
