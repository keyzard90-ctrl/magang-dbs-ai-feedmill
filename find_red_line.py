import cv2
import numpy as np

# Load the image
img = cv2.imread('garis line .jpeg')

# Convert to HSV
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Define range of red color in HSV
# Red has two ranges in HSV (0-10 and 170-180)
lower_red1 = np.array([0, 100, 100])
upper_red1 = np.array([10, 255, 255])
lower_red2 = np.array([160, 100, 100])
upper_red2 = np.array([180, 255, 255])

mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
mask = mask1 + mask2

# Find contours of the red line
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

if contours:
    # Filter for lines (very wide)
    wide_contours = [c for c in contours if cv2.boundingRect(c)[2] > 500]
    
    if wide_contours:
        largest_contour = max(wide_contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        print(f"Red Line Location:")
        print(f"Start X: {x}")
        print(f"End X: {x + w}")
        print(f"Y (Center): {y + h//2}")
        print(f"Thickness (H): {h}")
        print(f"Width (W): {w}")
    else:
        print("No wide red line found!")
else:
    print("No red line found!")
