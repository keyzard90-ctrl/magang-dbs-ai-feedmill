from ultralytics import YOLO

# Path model asli (.pt)
model_path = "karung-dimuat-detection-di-feedmill-yolo26n-seg-200e.pt"

print(f"Memuat model YOLOv8: {model_path}")
model = YOLO(model_path)

print("Memulai proses ekspor ke format TensorRT (.engine)...")
print("Catatan: Proses ini mungkin memakan waktu beberapa menit di NVIDIA Jetson.")

# Export model ke format TensorRT (FP16 direkomendasikan untuk Jetson agar FPS lebih tinggi)
model.export(
    format="engine",
    device="0",        # Gunakan GPU utama Jetson
    half=True,         # Gunakan presisi FP16 (performa lebih cepat tanpa mengurangi banyak akurasi)
    workspace=4        # Alokasi memori kerja (4 GB, sesuaikan dengan RAM Jetson)
)

print("Ekspor selesai! File .engine siap digunakan.")
