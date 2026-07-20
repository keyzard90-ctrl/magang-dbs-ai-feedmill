import cv2
import requests
import base64
import time
import random

video_path = "Hasil_Final_AI_13Menit_Compressed.mp4"
url = "http://127.0.0.1:5001/api/receive_data"

print(f"Memulai simulasi CCTV menggunakan video: {video_path}")
cap = cv2.VideoCapture(video_path)

if not cap.isOpened():
    print(f"Error: Tidak dapat membuka video {video_path}")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0 or fps != fps:
    fps = 25.0
delay = 1.0 / fps

frame_count = 0
total_counted = 0
next_increment = random.randint(30, 100) # frames until next sack

# Dimensi frame
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

while True:
    ret, frame = cap.read()
    if not ret:
        print("Video selesai, mengulang dari awal...")
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        total_counted = 0
        frame_count = 0
        next_increment = random.randint(30, 100)
        continue
        
    # Compress frame for transmission
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
    ret, buffer = cv2.imencode('.jpg', frame, encode_param)
    
    if ret:
        img_b64 = base64.b64encode(buffer).decode('utf-8')
        
        boxes = []
        if frame_count >= next_increment:
            total_counted += 1
            next_increment += random.randint(30, 200) # add another random gap
            # Send a mock box with badge to trigger the JS log event
            boxes.append({
                'id': total_counted,
                'bbox': [100, 100, 200, 200], # mock coordinates
                'badge': True
            })
            
        data = {
            'image': img_b64,
            'total_count': total_counted,
            'frame_width': width,
            'frame_height': height,
            'boxes': boxes,
            'status': 'Simulasi berjalan'
        }
        
        try:
            requests.post(url, json=data)
        except Exception as e:
            print(f"Gagal mengirim data ke server: {e}")
            break
            
    # Sleep but slightly faster than real-time to not lag the dashboard
    time.sleep(delay)
    
    frame_count += 1
    if frame_count % 50 == 0:
        print(f"Sedang memutar... ({frame_count} frames terkirim, karung: {total_counted})")
