import cv2
import numpy as np
import sys

img_path = 'WhatsApp Image 2026-07-10 at 10.03.21.jpeg'
img = cv2.imread(img_path)

if img is None:
    print(f"Failed to load {img_path}")
    sys.exit(1)

# Function to find lines of a specific color
def find_color_lines(hsv_img, lower, upper, color_name):
    mask = cv2.inRange(hsv_img, lower, upper)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    wide_contours = [c for c in contours if cv2.boundingRect(c)[2] > 200] # width > 200
    
    if wide_contours:
        largest_contour = max(wide_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        print(f"[{color_name} Line Found]")
        print(f"X: {x} to {x+w} | Y (Center): {y + h//2} | Width: {w} | Height: {h}")
        return y + h//2
    return None

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Blue
lower_blue = np.array([100, 150, 0])
upper_blue = np.array([140, 255, 255])
find_color_lines(hsv, lower_blue, upper_blue, "Blue")

# Red (two ranges)
lower_red1 = np.array([0, 150, 50])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([170, 150, 50])
upper_red2 = np.array([180, 255, 255])
mask_red = cv2.inRange(hsv, lower_red1, upper_red1) + cv2.inRange(hsv, lower_red2, upper_red2)
contours, _ = cv2.findContours(mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
wide_contours = [c for c in contours if cv2.boundingRect(c)[2] > 200]
if wide_contours:
    largest = max(wide_contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    print(f"[Red Line Found]")
    print(f"X: {x} to {x+w} | Y (Center): {y + h//2} | Width: {w} | Height: {h}")

# Green
lower_green = np.array([40, 100, 100])
upper_green = np.array([80, 255, 255])
find_color_lines(hsv, lower_green, upper_green, "Green")

