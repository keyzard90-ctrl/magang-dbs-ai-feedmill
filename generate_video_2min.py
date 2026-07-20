import cv2
import time
import numpy as np
import math
from ultralytics import YOLO

# ==========================================
# TRACKER MODULE
# ==========================================
class YOLOTracker:
    def __init__(self, model_path, tracker_config="bytetrack.yaml", max_area=150000):
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.max_area = max_area
        
    def track(self, frame, line_y=500, conf_base=0.3, conf_high=0.5):
        results = self.model.track(frame, persist=True, tracker=self.tracker_config, conf=conf_base, verbose=False)
        tracked_sacks = []
        raw_result = results[0] if results else None
        
        if raw_result and raw_result.boxes is not None and raw_result.boxes.id is not None:
            boxes = raw_result.boxes.xyxy.cpu().numpy()
            track_ids = raw_result.boxes.id.int().cpu().tolist()
            classes = raw_result.boxes.cls.int().cpu().tolist()
            confs = raw_result.boxes.conf.cpu().tolist()
            
            for bbox, t_id, cls, conf in zip(boxes, track_ids, classes, confs):
                if cls == 1: # 1 is sack
                    x1, y1, x2, y2 = bbox
                    w = x2 - x1
                    h = y2 - y1
                    area = w * h
                    if area > self.max_area:
                        continue
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
        self.track_states = {}
        self.counted_ids = set() 
        self.ignored_ids = set()
        self.total_count = 0
        self.frame_count = 0
        self.recent_drops = []
        
    def get_truck_zone(self, frame):
        h, w = frame.shape[:2]
        truck_zone = np.array([
            [int(w * 0.35), 0],                 
            [int(w * 0.72), 0],                 
            [int(w * 0.72), int(h * 0.55)],     
            [int(w * 0.35), int(h * 0.55)]      
        ], np.int32)
        return truck_zone

    def update(self, tracked_objects, frame):
        self.frame_count += 1
        truck_zone = self.get_truck_zone(frame)
        events = []
        for track in tracked_objects:
            track_id = track['id']
            bbox = track['bbox']
            
            if track_id in self.counted_ids or track_id in self.ignored_ids:
                continue
                
            center_x = int((bbox[0] + bbox[2]) / 2)
            center_y = int(bbox[1] + (bbox[3] - bbox[1]) * 0.7) 
            
            is_inside = cv2.pointPolygonTest(truck_zone, (center_x, center_y), False) >= 0
            
            if track_id not in self.track_states:
                if is_inside:
                    self.ignored_ids.add(track_id)
                    continue
                else:
                    self.track_states[track_id] = {'is_inside': is_inside, 'frames_outside': 1}
            else:
                was_inside = self.track_states[track_id]['is_inside']
                frames_outside = self.track_states[track_id].get('frames_outside', 0)
                
                if not is_inside:
                    self.track_states[track_id]['frames_outside'] = frames_outside + 1

                if not was_inside and is_inside:
                    if frames_outside >= 5:
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
                            self.ignored_ids.add(track_id) 
                    else:
                        self.ignored_ids.add(track_id) 
                
                self.track_states[track_id]['is_inside'] = is_inside
                        
        return events
        
    def draw(self, frame):
        truck_zone = self.get_truck_zone(frame)
        overlay = frame.copy()
        cv2.fillPoly(overlay, [truck_zone], (0, 255, 255))
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.polylines(frame, [truck_zone], True, (0, 255, 0), 2)
            
        cv2.putText(frame, f"TOTAL KARUNG: {self.total_count}", (50, 80), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 0), 8)
        cv2.putText(frame, f"TOTAL KARUNG: {self.total_count}", (50, 80), 
                    cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 255, 255), 3)
        return frame

def main():
    print("Loading models...")
    sack_tracker = YOLOTracker("karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt")
    truck_model = YOLO("truck-detector-feedmill.pt")
    
    counter = VectorCounter()
    
    input_video = "sample_5menit.mp4"
    output_video = "Hasil_Final_AI_2Menit_Truck_Sack.mp4"
    
    cap = cv2.VideoCapture(input_video)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0 or np.isnan(fps): fps = 25.0
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video, fourcc, fps, (width, height))
    
    max_frames = int(fps * 120) # 2 minutes
    frame_count = 0
    start_time = time.time()
    
    active_badges = {} 
    
    print(f"Processing video {input_video} for {max_frames} frames ({fps} fps)...")
    while cap.isOpened() and frame_count < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        # 1. Truck Detection (New Source)
        truck_results = truck_model(frame, conf=0.5, verbose=False)
        if truck_results and len(truck_results) > 0 and truck_results[0].boxes is not None:
            boxes = truck_results[0].boxes.xyxy.cpu().numpy()
            for bbox in boxes:
                tx1, ty1, tx2, ty2 = map(int, bbox)
                cv2.rectangle(frame, (tx1, ty1), (tx2, ty2), (255, 50, 50), 4) # Blue box for truck
                cv2.putText(frame, "TRUCK [AI]", (tx1, max(30, ty1 - 10)), 
                            cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 50, 50), 3)
            
        # 2. Sack Tracking & Counting (Original Source)
        tracked_objects, _ = sack_tracker.track(frame, line_y=560, conf_base=0.30, conf_high=0.55)
        events = counter.update(tracked_objects, frame)
        
        for event in events:
            if event['type'] == '+1':
                t_id = event['id']
                print(f"Frame {frame_count} | Karung #{t_id} MASUK! Total: {counter.total_count}")
                active_badges[t_id] = 20
                
        # Draw counter elements
        frame = counter.draw(frame)
        
        # Draw tracked sacks and badges
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
                    
            color = (0, 0, 255) if show_badge else (0, 165, 255) # Red if just counted, Orange otherwise
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"ID: {t_id}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
        out.write(frame)
        frame_count += 1
        
        if frame_count % 50 == 0:
            print(f"Processed {frame_count}/{max_frames} frames...")
            
    cap.release()
    out.release()
    print(f"Done! Saved to {output_video}")

if __name__ == '__main__':
    main()
