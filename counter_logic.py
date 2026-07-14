import cv2
import numpy as np

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
        import math
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
