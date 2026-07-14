import cv2
import numpy as np

img_path = 'WhatsApp Image 2026-07-10 at 10.03.21.jpeg'
img = cv2.imread(img_path)

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Looking for WhatsApp Blue (usually Cyan-Blue to Deep Blue, highly saturated)
lower_blue = np.array([90, 100, 100])
upper_blue = np.array([130, 255, 255])

mask = cv2.inRange(hsv, lower_blue, upper_blue)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

print("Looking for thin and wide blue lines...")
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    if w > 100 and h > 0:
        ratio = w / h
        if ratio > 5: # It's a line!
            print(f"FOUND DRAWN LINE! X: {x} to {x+w} | Y (Center): {y + h//2} | Width: {w}, Height: {h}, Ratio: {ratio:.1f}")

