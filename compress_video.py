import cv2
import subprocess

INPUT = "output_counting_5menit.mp4"
OUTPUT = "output_counting_5menit_compressed.mp4"

cap = cv2.VideoCapture(INPUT)
if not cap.isOpened():
    print("Gagal membuka video sumber.")
    exit()

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0: fps = 30

print(f"Mulai kompresi video dari {INPUT} ke {OUTPUT} menggunakan codec H.264...")
fourcc = cv2.VideoWriter_fourcc(*'avc1')
out = cv2.VideoWriter(OUTPUT, fourcc, fps, (width, height))

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    out.write(frame)
    frame_count += 1
    if frame_count % 500 == 0:
        print(f"Mengompres frame ke-{frame_count}...")

cap.release()
out.release()
print("Selesai! Membuka video terkompresi otomatis...")
subprocess.run(["open", OUTPUT])
