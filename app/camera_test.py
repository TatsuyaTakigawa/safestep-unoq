import os
import sys

import cv2

import safestep_config as cfg

OUT = os.environ.get(
    "SAFESTEP_CAMERA_TEST_OUT", os.path.join(cfg.ROOT_DIR, "camera_test.jpg")
)

src = cfg.camera_source()
print("Camera source:", src)
cap = cv2.VideoCapture(src)

if not cap.isOpened():
    print("Camera could not be opened.")
    sys.exit(1)

# The first frames of USB cameras are often dark, so skip a few.
ret, frame = False, None
for _ in range(10):
    ret, frame = cap.read()

print("Capture successful:", ret)

if ret:
    print("Image size (h, w, ch):", frame.shape)
    try:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        cv2.imwrite(OUT, frame)
        print("Saved:", OUT)
    except Exception as e:
        print(f"Could not save image ({type(e).__name__})")

cap.release()
sys.exit(0 if ret else 1)
