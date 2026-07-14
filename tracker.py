import numpy as np
from ultralytics import YOLO

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
