from ultralytics import YOLO

def main():
    model = YOLO('yolov8n.pt')
    results = model.train(
        data='/Users/macbookpro/Documents/magang-dbs-2026/truck-detector-feedmill/data.yaml',
        epochs=50,
        imgsz=640,
        project='/Users/macbookpro/Documents/magang-dbs-2026',
        name='truck-detector-training'
    )

if __name__ == '__main__':
    main()
