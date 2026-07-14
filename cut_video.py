import cv2
import time

input_path = "Camera2_16-32-45.mp4"
output_path = "Camera2_16-32-45_12menit.mp4"

cap = cv2.VideoCapture(input_path)
fps = cap.get(cv2.CAP_PROP_FPS)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

target_frames = int(12 * 60 * fps)
print(f"Total frames to process: {target_frames}")

count = 0
start_t = time.time()
while cap.isOpened() and count < target_frames:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)
    count += 1
    
    if count % 1000 == 0:
        elapsed = time.time() - start_t
        print(f"Processed {count}/{target_frames} frames... ({elapsed:.1f}s)")

cap.release()
out.release()
print("Done cutting video!")
