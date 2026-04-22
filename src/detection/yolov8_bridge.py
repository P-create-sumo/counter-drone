"""
YOLOv8 → Counter-Drone C2 Bridge
Runs YOLOv8 on camera/video feed, sends detections to the C2 webhook.
Deploy this on the edge sensor node (Raspberry Pi 5, Jetson Nano, etc.)
"""

import requests
import time
from ultralytics import YOLO

# Config
C2_WEBHOOK_URL = "https://YOUR_BASE44_APP/functions/threatWebhook"
SENSOR_LAT = 48.38       # base sensor location
SENSOR_LON = 31.165
CONFIDENCE_THRESHOLD = 0.65
CLASSES_OF_INTEREST = {"fpv_drone", "quadcopter", "fixed_wing", "loitering_munition"}
CLASSIFICATION_MAP = {
    "fpv_drone": "FPV",
    "quadcopter": "Quadcopter",
    "fixed_wing": "Fixed-Wing",
    "loitering_munition": "Loitering",
}

model = YOLO("yolov8n.pt")  # swap with fine-tuned drone model

def estimate_threat_position(bbox, frame_w, frame_h, alt_estimate_m=60):
    """
    Rough GPS estimate from bounding box position in frame.
    In production: use triangulation from multiple sensors or radar fusion.
    """
    cx = (bbox[0] + bbox[2]) / 2 / frame_w  # 0-1 horizontal
    cy = (bbox[1] + bbox[3]) / 2 / frame_h  # 0-1 vertical
    # Simple linear offset from sensor position (replace with proper geo math)
    lat = SENSOR_LAT + (0.5 - cy) * 0.01
    lon = SENSOR_LON + (cx - 0.5) * 0.015
    return lat, lon, alt_estimate_m

def send_to_c2(detection):
    try:
        r = requests.post(C2_WEBHOOK_URL, json=detection, timeout=5)
        data = r.json()
        print(f"[C2] {data.get('message', 'no message')} — drone: {data.get('assigned_drone')}")
    except Exception as e:
        print(f"[C2 ERROR] {e}")

def run(source=0):  # 0 = webcam, or path to video
    last_sent = {}
    for result in model.track(source=source, stream=True, persist=True):
        frame_h, frame_w = result.orig_shape
        for box in result.boxes:
            cls_name = model.names[int(box.cls)]
            conf = float(box.conf)
            if cls_name not in CLASSES_OF_INTEREST or conf < CONFIDENCE_THRESHOLD:
                continue
            track_id = int(box.id) if box.id is not None else 0
            # Debounce: don't spam same track
            if time.time() - last_sent.get(track_id, 0) < 5:
                continue
            last_sent[track_id] = time.time()
            lat, lon, alt = estimate_threat_position(box.xyxy[0].tolist(), frame_w, frame_h)
            detection = {
                "classification": CLASSIFICATION_MAP.get(cls_name, "Unknown"),
                "confidence": round(conf, 3),
                "lat": round(lat, 6), "lon": round(lon, 6),
                "alt_m": alt,
                "speed_kmh": 0,  # TODO: estimate from frame delta
                "heading_deg": 0,
                "source": "YOLOv8-optical"
            }
            print(f"[DETECT] {cls_name} conf={conf:.2f} → C2")
            send_to_c2(detection)

if __name__ == "__main__":
    run(source=0)
