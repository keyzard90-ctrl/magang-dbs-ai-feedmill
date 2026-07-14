import cv2
from ultralytics import YOLO

model = YOLO("karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt")
frame = cv2.imread("sample_frame.jpg")

results = model(frame)
boxes = results[0].boxes.xyxy.cpu().numpy()
classes = results[0].boxes.cls.int().cpu().tolist()

for bbox, cls in zip(boxes, classes):
    if cls == 1:
        x1, y1, x2, y2 = bbox
        w = x2 - x1
        h = y2 - y1
        area = w * h
        cy = y1 + h / 2.0
        print(f"Sack at cy={cy:.1f}, area={area:.1f}, size={w:.1f}x{h:.1f}")
