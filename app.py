from flask import Flask, render_template, jsonify, send_file, request, session, redirect, url_for, Response, stream_with_context
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
import webbrowser
import cv2
import time
import json
import datetime

app = Flask(__name__)
app.secret_key = 'enterprise_ai_key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
VIDEO_PATH = "rtsp://admin:K0l0r4n123@10.38.250.21/cam/realmonitor?channel=1&subtype=1" # Live RTSP Stream

# Global state untuk menyimpan data AI terbaru
latest_ai_data = {}
latest_frame = None

import threading
frame_lock = threading.Lock()

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'keyganteng' and password == 'key123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            error = 'Username atau Password salah!'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/ai-settings')
def ai_settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('ai_settings.html')

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    
    # Generate Indonesian date format manually for safety
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    today_label = f"{datetime.date.today().day} {months[datetime.date.today().month - 1]} {datetime.date.today().year}"
    
    recent_dates = [
        {"date": today_str, "label": "Hari Ini: " + today_label, "desc": "Live Stream Real-Time", "status": "Tersedia", "status_class": "status-badge-success"},
        {"date": "2026-06-27", "label": "27 Juni 2026", "desc": "Arsip Rekaman", "status": "Tersedia", "status_class": "status-badge-warning"},
    ]
    return render_template('home.html', recent_dates=recent_dates, today_str=today_str)

@app.route('/report/<date>')
def report(date):
    today_str = datetime.date.today().strftime('%Y-%m-%d')
    months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    try:
        # Parse YYYY-MM-DD
        d = datetime.datetime.strptime(date, '%Y-%m-%d')
        formatted_date = f"{d.day} {months[d.month - 1]} {d.year}"
    except:
        formatted_date = date
        
    is_live = (date == today_str)
        
    return render_template('report.html', date=formatted_date, is_live=is_live)

import base64

@app.route('/api/receive_data', methods=['POST'])
def receive_data():
    global latest_ai_data, latest_frame
    try:
        data = request.json
        if data and 'image' in data:
            img_data = base64.b64decode(data['image'])
            with frame_lock:
                latest_frame = img_data
            del data['image']
            
        latest_ai_data = data
        return jsonify({"status": "success"})
    except Exception as e:
        print("ERROR in receive_data:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/stream_data')
def stream_data():
    def generate():
        try:
            while True:
                yield f"data: {json.dumps(latest_ai_data)}\n\n"
                time.sleep(0.04) # ~25 FPS
        except GeneratorExit:
            pass
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

def gen_frames():
    try:
        # Wait for the first frame so Safari doesn't mark the stream as broken
        while latest_frame is None:
            time.sleep(0.1)
            
        while True:
            with frame_lock:
                frame_bytes = latest_frame
                
            if frame_bytes is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)
    except GeneratorExit:
        pass

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Auto-open browser
    import threading
    import time
    def open_browser():
        time.sleep(1)
        webbrowser.open_new('http://127.0.0.1:5001/')
    
    threading.Thread(target=open_browser).start()
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
