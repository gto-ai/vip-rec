from pathlib import Path
from deepface import DeepFace
from config import BASE, DATA

image_folder = Path(DATA, 'vip_images')

result = DeepFace.verify(
    img1_path=str(Path(image_folder, 'alex-lacamoire.png')),
    img2_path=str(Path(image_folder, 'alex-lacamoire.png')),
    model_name="ArcFace",
    detector_backend="retinaface"
)

print(result)

dfs = DeepFace.find(img_path="img1.jpg", db_path="C:/my_db")
