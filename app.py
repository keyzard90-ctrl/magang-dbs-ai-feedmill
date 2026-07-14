from flask import Flask, render_template, jsonify, send_file, request, session, redirect, url_for
import os
import webbrowser

app = Flask(__name__)
app.secret_key = 'enterprise_ai_key'
app.config['TEMPLATES_AUTO_RELOAD'] = True
VIDEO_PATH = "Hasil_Final_AI_12Menit_Fixed.mp4"

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
    recent_dates = [
        {"date": "2026-06-27", "label": "27 Juni 2026", "desc": "Video Durasi 12:00 Menit", "status": "Tersedia", "status_class": "status-badge-success"},
        {"date": "2026-06-26", "label": "26 Juni 2026", "desc": "Video Durasi 08:30 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
        {"date": "2026-06-25", "label": "25 Juni 2026", "desc": "Video Durasi 10:15 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
        {"date": "2026-06-24", "label": "24 Juni 2026", "desc": "Video Durasi 11:45 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
        {"date": "2026-06-23", "label": "23 Juni 2026", "desc": "Video Durasi 09:20 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
        {"date": "2026-06-22", "label": "22 Juni 2026", "desc": "Video Durasi 12:00 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
        {"date": "2026-06-21", "label": "21 Juni 2026", "desc": "Video Durasi 07:10 Menit", "status": "Dummy Data", "status_class": "status-badge-warning"},
    ]
    return render_template('home.html', recent_dates=recent_dates)

@app.route('/report/<date>')
def report(date):
    if date == '2026-06-27':
        return render_template('report.html', date=date)
    else:
        return render_template('dummy.html', date=date)

@app.route('/api/stats')
def stats():
    return jsonify({
        'total_sacks': 165,
        'accuracy': '90.0%',
        'duration': '12:00',
        'avg_per_min': round(165/12, 1)
    })

@app.route('/api/logs')
def get_logs():
    logs = []
    try:
        with open('actual_logs.txt', 'r') as f:
            for line in f:
                parts = line.strip().split('|')
                if len(parts) < 2: continue
                frame_str = parts[0].replace('Frame', '').strip()
                karung_str = parts[1].split('MASUK')[0].replace('Karung #', '').strip()
                frame = int(frame_str)
                t_id = int(karung_str)
                sec = round(frame / 25.0, 2)
                logs.append({"time": sec, "id": t_id})
    except:
        pass
    return jsonify(logs)

@app.route('/video')
def video():
    if not os.path.exists(VIDEO_PATH):
        fallback = "Hasil_Final_AI_12Menit.mp4"
        if os.path.exists(fallback):
            return send_file(fallback, mimetype='video/mp4')
        return "Video not found", 404
    return send_file(VIDEO_PATH, mimetype='video/mp4')

if __name__ == '__main__':
    # Auto-open browser
    import threading
    import time
    def open_browser():
        time.sleep(1)
        webbrowser.open_new('http://127.0.0.1:5001/')
    
    threading.Thread(target=open_browser).start()
    app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
