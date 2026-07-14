import cv2
import numpy as np

# Load full frame
frame = cv2.imread('/Users/macbookpro/Documents/magang-dbs-2026/frame_sample.jpg')
if frame is None:
    print("Failed to load frame_sample.jpg")
    exit()

# Load screenshot
template = cv2.imread('/Users/macbookpro/Desktop/Jepretan Layar 2026-07-10 pukul 15.03.59.png')
if template is None:
    print("Failed to load template")
    exit()

# Resize template if it's too large, but wait, screenshot is usually smaller or exact scale
# Let's try direct template matching on Grayscale
frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

# The screenshot might be taken from the video player which could be scaled!
# We can't guarantee scale. We can just use the user's WhatsApp image?
# Actually, let's just create an interactive script that generates the coordinates.
# But I can't interact.
# Let's just create a very precise polygon based on my understanding of perspective.
