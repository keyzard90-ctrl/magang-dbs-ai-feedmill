import cv2
import numpy as np

def find_polygon(img_path):
    print(f"\nAnalyzing: {img_path}")
    img = cv2.imread(img_path)
    if img is None:
        print("Failed to load image")
        return
        
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define range for pure green color (usually user drawings are bright green)
    lower_green = np.array([35, 100, 100])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("No green lines found.")
        return
        
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > 100: # Filter small noise
            hull = cv2.convexHull(contour)
            epsilon = 0.05 * cv2.arcLength(hull, True)
            approx = cv2.approxPolyDP(hull, epsilon, True)
            
            print(f"\nContour {i} (Area: {area}):")
            points = [pt[0] for pt in approx]
            for pt in points:
                print(f"({pt[0]}, {pt[1]})")

find_polygon("/Users/macbookpro/Desktop/Jepretan Layar 2026-07-10 pukul 15.03.59.png")
find_polygon("/Users/macbookpro/Documents/magang-dbs-2026/WhatsApp Image 2026-07-10 at 15.09.20.jpeg")
