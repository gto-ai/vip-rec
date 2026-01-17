import cv2
import numpy as np
from pathlib import Path

def remove_bg_and_crop_face(
    img_bgr: np.ndarray,
    yunet_onnx: str,
    selfie_onnx: str,
    out_size: int = 512,
    face_margin: float = 1.6,  # enlarge crop around face box
):
    h, w = img_bgr.shape[:2]

    # --- 1) Background removal with Selfie Segmentation ---
    seg = cv2.dnn.readNetFromONNX(selfie_onnx)

    # Most selfie-seg models expect RGB, normalized, specific input size.
    # We'll follow a common pattern: resize to 256x256 and normalize to [0,1].
    inp_w, inp_h = 256, 256
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    blob = cv2.dnn.blobFromImage(img_rgb, scalefactor=1.0/255.0, size=(inp_w, inp_h))
    seg.setInput(blob)
    mask = seg.forward()  # shape often: (1,1,H,W) or (1,2,H,W)

    # Handle common output shapes
    mask = np.squeeze(mask)
    if mask.ndim == 3:  # e.g., (2,H,W) -> take foreground channel
        # assume channel 1 is foreground prob in a 2-class output
        mask = mask[1]

    # Resize mask back to image size
    mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)

    # Convert to 0..255 uint8 alpha mask
    alpha = np.clip(mask * 255.0, 0, 255).astype(np.uint8)

    # Optional: clean edges a bit
    alpha = cv2.GaussianBlur(alpha, (0, 0), 2)
    _, alpha = cv2.threshold(alpha, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Compose BGRA with transparent background
    bgra = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2BGRA)
    bgra[:, :, 3] = alpha

    # --- 2) Face detection with YuNet ---
    detector = cv2.FaceDetectorYN.create(
        yunet_onnx,
        "",
        (w, h),
        score_threshold=0.8,
        nms_threshold=0.3,
        top_k=5000,
    )
    _, faces = detector.detect(img_bgr)

    if faces is None or len(faces) == 0:
        # No face found; return bg-removed full image
        return bgra

    # Pick largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, bw, bh = faces[0][:4].astype(int)

    # Expand crop
    cx, cy = x + bw / 2, y + bh / 2
    side = max(bw, bh) * face_margin
    x1 = int(max(0, cx - side / 2))
    y1 = int(max(0, cy - side / 2))
    x2 = int(min(w, cx + side / 2))
    y2 = int(min(h, cy + side / 2))

    cropped = bgra[y1:y2, x1:x2]
    if cropped.size == 0:
        return bgra

    # Pad to square then resize
    ch, cw = cropped.shape[:2]
    s = max(ch, cw)
    pad_t = (s - ch) // 2
    pad_b = s - ch - pad_t
    pad_l = (s - cw) // 2
    pad_r = s - cw - pad_l
    cropped = cv2.copyMakeBorder(cropped, pad_t, pad_b, pad_l, pad_r, cv2.BORDER_CONSTANT, value=(0,0,0,0))

    cropped = cv2.resize(cropped, (out_size, out_size), interpolation=cv2.INTER_AREA)
    return cropped

def main():
    img_path = "/home/rfouyang/workspace/data/vip_images/Colonel Chong Shi Hao 1.jpg"
    out_path = "/home/rfouyang/workspace/data/face_no_bg.png"
    yunet_onnx = "models/face_detection_yunet_2023mar.onnx"
    selfie_onnx = "models/selfie_segmentation.onnx"

    img = cv2.imread(img_path)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {img_path}")

    result = remove_bg_and_crop_face(img, yunet_onnx, selfie_onnx)
    cv2.imwrite(out_path, result)  # PNG keeps transparency
    print("Saved:", out_path)

if __name__ == "__main__":
    main()
