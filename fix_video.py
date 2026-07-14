from moviepy import VideoFileClip
import subprocess

INPUT = "Hasil_Final_AI_12Menit.mp4"
OUTPUT = "Hasil_Final_AI_12Menit_Fixed.mp4"

print(f"Mulai konversi dan kompresi {INPUT} menjadi standar MP4 yang didukung Mac...")
try:
    video = VideoFileClip(INPUT)
    # Gunakan libx264 yang 100% didukung QuickTime Mac
    video.write_videofile(OUTPUT, codec="libx264", preset="fast", audio=False)
    print("Berhasil diperbaiki! Membuka video...")
    subprocess.run(["open", OUTPUT])
except Exception as e:
    print(f"Error saat mengonversi video: {e}")
