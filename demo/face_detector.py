from ultralytics import YOLO
import cv2

# Load a face model (example: YOLOv8-face)
model = YOLO("yolov8n.pt")  # change path if needed

cap = cv2.VideoCapture(0)  # /dev/video0

if not cap.isOpened():
    raise RuntimeError("Cannot open /dev/video1")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, conf=0.4)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    cv2.imshow("YOLO Face Detection (/dev/video1)", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
