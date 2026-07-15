import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
import cv2
import time
import numpy as np
import math
from ultralytics import YOLO
import requests
import base64
import threading

# Use a session to prevent connection exhaustion from hundreds of POSTs per second
http_session = requests.Session()

is_sending = False
def send_payload_async(payload):
    global is_sending
    try:
        http_session.post("http://127.0.0.1:5001/api/receive_data", json=payload, timeout=0.5)
    except Exception:
        pass
    finally:
        is_sending = False

# ==========================================
# TRACKER MODULE
# ==========================================
def calculate_iou(box1, box2):
    """
    Calculate IoU between two bounding boxes [x1, y1, x2, y2]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0, x2 - x1) * max(0, y2 - y1)
    
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    
    union = area1 + area2 - intersection
    if union == 0:
        return 0
    return intersection / union

class YOLOTracker:
    def __init__(self, model_path, tracker_config="bytetrack.yaml", max_area=150000):
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.max_area = max_area
        
    def track(self, frame, line_y=500, conf_base=0.3, conf_high=0.5):
        """
        Runs tracking and applies Layer 1: Anti-Human Filter
        """
        results = self.model.track(frame, persist=True, tracker=self.tracker_config, conf=conf_base, verbose=False)
        
        tracked_sacks = []
        person_boxes = []
        raw_result = results[0] if results else None
        
        if raw_result and raw_result.boxes is not None and raw_result.boxes.id is not None:
            boxes = raw_result.boxes.xyxy.cpu().numpy()
            track_ids = raw_result.boxes.id.int().cpu().tolist()
            classes = raw_result.boxes.cls.int().cpu().tolist()
            confs = raw_result.boxes.conf.cpu().tolist()
            
            # First pass: collect all person boxes for IoU masking
            for bbox, cls in zip(boxes, classes):
                if cls == 0: # 0 is person
                    person_boxes.append(bbox)
                    
            # Second pass: filter sacks
            for bbox, t_id, cls, conf in zip(boxes, track_ids, classes, confs):
                if cls == 1: # 1 is sack
                    x1, y1, x2, y2 = bbox
                    w = x2 - x1
                    h = y2 - y1
                    area = w * h
                    cy = y1 + h / 2.0
                    
                    # 1. Filter Luas Area Maksimal (Max Area Limit)
                    if area > self.max_area:
                        continue
                        
                    # 2. Confidence Threshold near line
                    # DISABLED: Membuang track di dekat garis justru membuat ID tereset dan karung terlewat saat bergerak cepat

                    # 3. Filter Tumpang Tindih Kelas (Negative IoU Masking)
                    # DISABLED: Karena pekerja memang selalu memanggul karung, overlap pasti terjadi
                    # sehingga filter ini justru menghapus karung yang valid.
                    # (Filter Max Area sudah cukup untuk mencegah pekerja dikenali sebagai karung).
                        
                    tracked_sacks.append({
                        'id': t_id,
                        'bbox': bbox,
                        'conf': conf
                    })
                    
        return tracked_sacks, raw_result


# ==========================================
# COUNTER LOGIC MODULE
# ==========================================
class VectorCounter:
    def __init__(self):
        self.track_states = {} # id -> {'is_inside': bool, 'frames_outside': int}
        self.counted_ids = set() 
        self.ignored_ids = set() # Menampung ID yang lahir di dalam zona
        self.total_count = 0
        self.frame_count = 0
        self.recent_drops = [] # list of {'frame': int, 'x': int, 'y': int}
        
    def get_truck_zone(self, frame):
        h, w = frame.shape[:2]
        truck_zone = np.array([
            [int(w * 0.35), 0],                 # Kiri atas (mentok ujung atas kamera)
            [int(w * 0.72), 0],                 # Kanan atas (mentok ujung atas kamera)
            [int(w * 0.72), int(h * 0.55)],     # Kanan bawah (tetap)
            [int(w * 0.35), int(h * 0.55)]      # Kiri bawah (tetap)
        ], np.int32)
        return truck_zone

    def update(self, tracked_objects, frame):
        self.frame_count += 1
        truck_zone = self.get_truck_zone(frame)
        events = []
        for track in tracked_objects:
            track_id = track['id']
            bbox = track['bbox']
            
            # 3. Kunci Eksekusi Instan (Break Loop)
            if track_id in self.counted_ids:
                continue
            if track_id in self.ignored_ids:
                continue
                
            center_x = int((bbox[0] + bbox[2]) / 2)
            center_y = int(bbox[1] + (bbox[3] - bbox[1]) * 0.7) # Evaluasi agak ke bawah (lebih stabil mengikuti beban jatuh)
            
            # Evaluasi titik pusat
            is_inside = cv2.pointPolygonTest(truck_zone, (center_x, center_y), False) >= 0
            
            if track_id not in self.track_states:
                # 2. Filter 'ID Mendadak' di Dalam Zona (Origin Check)
                if is_inside:
                    self.ignored_ids.add(track_id)
                    continue
                else:
                    self.track_states[track_id] = {'is_inside': is_inside, 'frames_outside': 1}
            else:
                # 1. Logika Transisi (Dari Luar ke Dalam)
                was_inside = self.track_states[track_id]['is_inside']
                frames_outside = self.track_states[track_id].get('frames_outside', 0)
                
                if not is_inside:
                    self.track_states[track_id]['frames_outside'] = frames_outside + 1

                if not was_inside and is_inside:
                    # Syarat 1: Umur di luar zona minimal 5 frame
                    if frames_outside >= 5:
                        # Syarat 2: Spatial-Temporal Suppression (Jarak < 100px dalam 15 frame)
                        is_duplicate = False
                        for drop in self.recent_drops:
                            if (self.frame_count - drop['frame']) <= 15:
                                dist = math.hypot(center_x - drop['x'], center_y - drop['y'])
                                if dist < 100:
                                    is_duplicate = True
                                    break
                                    
                        if not is_duplicate:
                            self.total_count += 1
                            self.counted_ids.add(track_id)
                            self.recent_drops.append({'frame': self.frame_count, 'x': center_x, 'y': center_y})
                            events.append({'id': track_id, 'type': '+1', 'bbox': bbox})
                        else:
                            self.ignored_ids.add(track_id) # Duplikat diabaikan seumur hidup
                    else:
                        self.ignored_ids.add(track_id) # Lahir di perbatasan diabaikan
                
                # Simpan histori status posisi untuk frame berikutnya
                self.track_states[track_id]['is_inside'] = is_inside
                        
        return events
        
    def draw(self, frame):
        truck_zone = self.get_truck_zone(frame)
        
        # Efek Kaca Kuning Transparan (Overlay)
        overlay = frame.copy()
        cv2.fillPoly(overlay, [truck_zone], (0, 255, 255))
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        
        # Garis Tepi Hijau
        cv2.polylines(frame, [truck_zone], True, (0, 255, 0), 2)
            
        # Teks TOTAL KARUNG di pojok kiri atas
        cv2.putText(frame, f"TOTAL KARUNG: {self.total_count}", (50, 80), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 0), 8) # Hitam border
        cv2.putText(frame, f"TOTAL KARUNG: {self.total_count}", (50, 80), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 255), 3) # Kuning teks
        return frame


# ==========================================
# MAIN APPLICATION MODULE
# ==========================================
# ----------------- CONFIGURATION -----------------
VIDEO_INPUT = "rtsp://admin:K0l0r4n123@10.38.250.21/cam/realmonitor?channel=1&subtype=1"
MODEL_PATH = "karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.engine"

# Konstanta Zona Kotak Bak Truk kini dihitung dinamis di fungsi get_truck_zone()

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
        
        # Send raw frame to app.py to avoid double RTSP connection
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        raw_frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        payload = {
            "total_count": counter.total_count,
            "zone": counter.get_truck_zone(frame).tolist(),
            "boxes": [],
            "frame_width": width,
            "frame_height": height,
            "image": raw_frame_b64
        }
        
        # Data preparation (No OpenCV drawing)
        for sack in tracked_objects:
            t_id = sack['id']
            x1, y1, x2, y2 = map(int, sack['bbox'])
            
            show_badge = False
            if t_id in active_badges:
                if active_badges[t_id] > 0:
                    show_badge = True
                    active_badges[t_id] -= 1
                else:
                    del active_badges[t_id]
                    
            payload["boxes"].append({
                "id": t_id,
                "bbox": [x1, y1, x2, y2],
                "badge": show_badge
            })
            
        global is_sending
        if not is_sending:
            is_sending = True
            threading.Thread(target=send_payload_async, args=(payload,), daemon=True).start()
        
        # Penulisan video dinonaktifkan untuk menghemat memori
        frame_count += 1
        
        if frame_count % 300 == 0:
            elapsed = time.time() - start_time
            print(f"Processed {frame_count} frames... ({elapsed:.1f}s)")
            
    cap.release()
    print("Proses selesai.")

if __name__ == "__main__":
    main()
