import json

fps = 25.0
logs = []
with open('actual_logs.txt', 'r') as f:
    for line in f:
        try:
            parts = line.strip().split('|')
            if len(parts) < 2: continue
            frame_str = parts[0].replace('Frame', '').strip()
            karung_str = parts[1].split('MASUK')[0].replace('Karung #', '').strip()
            
            frame = int(frame_str)
            t_id = int(karung_str)
            sec = round(frame / fps, 2)
            
            logs.append({"time": sec, "id": t_id})
        except Exception as e:
            pass

with open('static/js/actual_logs.js', 'w') as f:
    f.write(f"const ACTUAL_LOGS = {json.dumps(logs)};\n")
