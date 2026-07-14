import cv2
import numpy as np

img = cv2.imread('/Users/macbookpro/Desktop/Jepretan Layar 2026-07-10 pukul 15.03.59.png')
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
lower_green = np.array([35, 100, 100])
upper_green = np.array([85, 255, 255])
mask = cv2.inRange(hsv, lower_green, upper_green)

# Find bounding box of all green pixels
coords = cv2.findNonZero(mask)
if coords is not None:
    x, y, w, h = cv2.boundingRect(coords)
    print(f"Jepretan Layar - Bounding Box of ALL green pixels: X={x}, Y={y}, W={w}, H={h}")
else:
    print("No green in Jepretan Layar")

img2 = cv2.imread('/Users/macbookpro/Documents/magang-dbs-2026/WhatsApp Image 2026-07-10 at 15.09.20.jpeg')
hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
mask2 = cv2.inRange(hsv2, lower_green, upper_green)
coords2 = cv2.findNonZero(mask2)
if coords2 is not None:
    x, y, w, h = cv2.boundingRect(coords2)
    print(f"WhatsApp Image - Bounding Box of ALL green pixels: X={x}, Y={y}, W={w}, H={h}")
else:
    print("No green in WhatsApp Image")
