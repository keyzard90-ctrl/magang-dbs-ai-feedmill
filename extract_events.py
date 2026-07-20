import cv2
import json
import math
import numpy as np
from ultralytics import YOLO

class YOLOTracker:
    def __init__(self, model_path, tracker_config="bytetrack.yaml", max_area=150000):
        self.model = YOLO(model_path)
        self.tracker_config = tracker_config
        self.max_area = max_area
        
    def track(self, frame, conf_base=0.25):
        results = self.model.track(frame, persist=True, tracker=self.tracker_config, conf=conf_base, verbose=False)
        tracked_sacks = []
        raw_result = results[0] if results else None
        
        if raw_result and raw_result.boxes is not None and raw_result.boxes.id is not None:
            boxes = raw_result.boxes.xyxy.cpu().numpy()
            track_ids = raw_result.boxes.id.int().cpu().tolist()
            classes = raw_result.boxes.cls.int().cpu().tolist()
            
            for bbox, t_id, cls in zip(boxes, track_ids, classes):
                if cls == 1: 
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    if (w * h) > self.max_area:
                        continue
                    tracked_sacks.append({'id': t_id, 'bbox': bbox})
        return tracked_sacks

class VectorCounter:
    def __init__(self):
        self.track_states = {}
        self.counted_ids = set() 
        self.ignored_ids = set()
        self.total_count = 0
        self.frame_count = 0
        self.recent_drops = []
        
    def get_truck_zone(self, w, h):
        return np.array([
            [int(w * 0.33), 0],                 
            [int(w * 0.74), 0],                 
            [int(w * 0.74), int(h * 0.58)],     
            [int(w * 0.33), int(h * 0.58)]      
        ], np.int32)

    def update(self, tracked_objects, w, h):
        self.frame_count += 1
        truck_zone = self.get_truck_zone(w, h)
        events = []
        for track in tracked_objects:
            track_id = track['id']
            bbox = track['bbox']
            
            if track_id in self.counted_ids or track_id in self.ignored_ids:
                continue
                
            center_x = int((bbox[0] + bbox[2]) / 2)
            center_y = int(bbox[1] + (bbox[3] - bbox[1]) * 0.6) 
            
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
                    if frames_outside >= 3:
                        is_duplicate = False
                        for drop in self.recent_drops:
                            if (self.frame_count - drop['frame']) <= 12:
                                dist = math.hypot(center_x - drop['x'], center_y - drop['y'])
                                if dist < 70:
                                    is_duplicate = True
                                    break
                                    
                        if not is_duplicate:
                            self.total_count += 1
                            self.counted_ids.add(track_id)
                            self.recent_drops.append({'frame': self.frame_count, 'x': center_x, 'y': center_y})
                            events.append({'id': track_id})
                        else:
                            self.ignored_ids.add(track_id) 
                    else:
                        self.ignored_ids.add(track_id) 
                
                self.track_states[track_id]['is_inside'] = is_inside
                        
        return events

def main():
    print("Loading model for fast extraction...")
    sack_tracker = YOLOTracker("karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt")
    counter = VectorCounter()
    
    input_video = "Camera2_16-32-45.mp4"
    cap = cv2.VideoCapture(input_video)
    
    if not cap.isOpened():
        print("Video not found!")
        return
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    max_frames = int(fps * 13 * 60)
    
    all_events = []
    
    print("Extracting data...")
    while cap.isOpened() and counter.frame_count < max_frames:
        ret, frame = cap.read()
        if not ret: break
        
        tracked_objects = sack_tracker.track(frame)
        events = counter.update(tracked_objects, w, h)
        
        for e in events:
            time_sec = counter.frame_count / fps
            all_events.append({
                "time": time_sec,
                "id": counter.total_count, # use total_count as logical ID so it increments 1, 2, 3...
                "real_id": e['id'],
                "total_sacks": counter.total_count
            })
            print(f"[{time_sec:.1f}s] Karung Masuk! Total: {counter.total_count}")
            
        if counter.frame_count % 500 == 0:
            print(f"Processed {counter.frame_count}/{max_frames} frames...")
            
    cap.release()
    
    # Save JSON
    import os
    os.makedirs('static/data', exist_ok=True)
    with open('static/data/events.json', 'w') as f:
        json.dump(all_events, f)
        
    print(f"Extraction complete! Saved {len(all_events)} events.")

if __name__ == '__main__':
    main()
