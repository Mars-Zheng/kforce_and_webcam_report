import cv2
import os
import datetime

# === Setup ===
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("❌ Cannot access camera.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

# === Output path ===
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_folder = "recorded_videos"
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, f"webcam_{timestamp}.mp4")

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = None
recording = False

cv2.namedWindow("Webcam", cv2.WINDOW_NORMAL)


print("🎥 Press 'r' to start recording, 's' to stop, and 'q' to quit.")

# === Main Loop ===
while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠ Frame capture failed.")
        break

    # === Draw vertical center line ===
    height, width = frame.shape[:2]
    center_x = width // 2
    cv2.line(frame, (center_x, 0), (center_x, height), (0, 255, 0), 2)  # Green vertical line

    cv2.imshow("Webcam", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('r') and not recording:
        print("🔴 Recording started...")
        out = cv2.VideoWriter(output_path, fourcc, 30.0, (width, height))
        recording = True

    elif key == ord('s') and recording:
        print("🛑 Recording stopped.")
        recording = False
        out.release()

    elif key == ord('q'):
        print("👋 Exiting...")
        break

    if recording:
        out.write(frame)

# === Cleanup ===
if recording and out:
    out.release()
cap.release()
cv2.destroyAllWindows()

print(f"✅ Video saved to: {output_path}")
