import cv2
import subprocess

RTSP_URL = "rtsp://localhost:8554/mystream"

# ffmpeg command - VLC compatible (YUV420p + Baseline)
command = [
    "ffmpeg",
    "-y",
    "-f", "rawvideo",
    "-pixel_format", "bgr24",
    "-video_size", "640x480",
    "-framerate", "30",
    "-i", "-",                      # read from stdin

    # H.264 encoding (VLC-compatible)
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-pix_fmt", "yuv420p",
    "-profile:v", "baseline",

    # RTSP output
    "-f", "rtsp",
    RTSP_URL
]

# start ffmpeg
ffmpeg = subprocess.Popen(command, stdin=subprocess.PIPE)

# open camera
cap = cv2.VideoCapture("/dev/video0")
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

print(f"Pushing stream to: {RTSP_URL}")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    ffmpeg.stdin.write(frame.tobytes())
