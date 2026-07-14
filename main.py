import cv2
import time
from tracker import YOLOTracker
from counter_logic import VectorCounter

# ----------------- CONFIGURATION -----------------
VIDEO_INPUT = "Camera2_16-32-45_12menit.mp4"
VIDEO_OUTPUT = "Hasil_Final_AI_12Menit.mp4"
MODEL_PATH = "karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt"

# Konstanta Zona Kotak Bak Truk kini dihitung dinamis di counter_logic.py

def main():
    print("Inisialisasi Model YOLOv8 & ByteTrack (Layer 1 Active)...")
    tracker = YOLOTracker(MODEL_PATH)
    
    print("Inisialisasi Poligon & Logika Kalkulasi (Layer 2 Active)...")
    counter = VectorCounter()
    
    cap = cv2.VideoCapture(VIDEO_INPUT)
    if not cap.isOpened():
        print(f"Gagal membuka video {VIDEO_INPUT}")
        return
        
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    out = cv2.VideoWriter(VIDEO_OUTPUT, fourcc, fps, (width, height))
    
    frame_count = 0
    start_time = time.time()
    
    # Layer 3: Visual Badges
    active_badges = {} # track_id -> frames_left
    
    print("Mulai memproses video...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        tracked_objects, raw_result = tracker.track(frame, line_y=560, conf_base=0.30, conf_high=0.55)
        
        events = counter.update(tracked_objects, frame)
        
        for event in events:
            if event['type'] == '+1':
                t_id = event['id']
                print(f"Frame {frame_count} | Karung #{t_id} MASUK! Total: {counter.total_count}")
                # Layer 3: Activate Badge for 20 frames
                active_badges[t_id] = 20
        
        # Bounding box & Badge rendering
        for sack in tracked_objects:
            t_id = sack['id']
            x1, y1, x2, y2 = map(int, sack['bbox'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"ID: {t_id}", (x1, y1 - 10), 

                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                            
            # Layer 3: Draw Neon Green '+1' Badge
            if t_id in active_badges:
                if active_badges[t_id] > 0:
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    cv2.putText(frame, "+1", (cx - 25, cy + 15), 
                                cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 255), 3)
                    active_badges[t_id] -= 1
                else:
                    del active_badges[t_id]
                            
        frame = counter.draw(frame)
        
        out.write(frame)
        frame_count += 1
        
        if frame_count % 300 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {frame_count} frames... ({elapsed:.1f}s)")
            
    cap.release()
    out.release()
    print("Proses selesai. Video output disimpan sebagai:", VIDEO_OUTPUT)
    
    # Membuka video secara otomatis di macOS
    import subprocess
    print("Membuka video secara otomatis...")
    subprocess.run(["open", VIDEO_OUTPUT])

if __name__ == "__main__":
    main()
