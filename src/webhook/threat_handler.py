"""
Counter-Drone Interceptor — Threat Webhook Handler
Mirrors the Base44 backend function logic in pure Python.
Use this for local testing or self-hosted deployment.
"""

from flask import Flask, request, jsonify
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory state (replace with DB in production)
interceptors = [
    {"id": "INT-001", "status": "Standby", "battery": 98, "lat": 48.380, "lon": 31.165, "kills": 3},
    {"id": "INT-002", "status": "Standby", "battery": 91, "lat": 48.382, "lon": 31.170, "kills": 1},
    {"id": "INT-003", "status": "Standby", "battery": 100, "lat": 48.384, "lon": 31.159, "kills": 0},
]
threats = []


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))


def get_threat_level(cls, conf, speed):
    if cls == "FPV" and conf > 0.85:
        return "CRITICAL"
    if cls == "Loitering" or speed > 80:
        return "HIGH"
    if conf > 0.7:
        return "MEDIUM"
    return "LOW"


@app.route("/webhook/threat", methods=["POST"])
def threat_webhook():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    if not lat or not lon:
        return jsonify({"error": "lat/lon required"}), 400

    cls = data.get("classification", "Unknown")
    conf = data.get("confidence", 0.5)
    speed = data.get("speed_kmh", 0)

    threat_id = f"THR-{uuid.uuid4().hex[:6].upper()}"
    threat = {
        "id": threat_id,
        "classification": cls,
        "confidence": conf,
        "lat": lat, "lon": lon,
        "alt_m": data.get("alt_m", 0),
        "speed_kmh": speed,
        "heading_deg": data.get("heading_deg", 0),
        "status": "Detected",
        "assigned_drone": None,
        "detected_at": datetime.utcnow().isoformat(),
        "source": data.get("source", "external"),
        "threat_level": get_threat_level(cls, conf, speed)
    }
    threats.append(threat)

    # Find nearest available interceptor
    available = [d for d in interceptors if d["status"] == "Standby" and d["battery"] > 20]
    if not available:
        return jsonify({"success": True, "threat_id": threat_id, "assigned_drone": None, "message": "No interceptor available"})

    nearest = min(available, key=lambda d: haversine_km(lat, lon, d["lat"], d["lon"]))
    dist = haversine_km(lat, lon, nearest["lat"], nearest["lon"])
    eta = int((dist / 80) * 3600)

    nearest["status"] = "InFlight"
    nearest["assigned_threat"] = threat_id
    threat["assigned_drone"] = nearest["id"]
    threat["status"] = "Tracked"

    return jsonify({
        "success": True,
        "threat_id": threat_id,
        "assigned_drone": nearest["id"],
        "distance_km": round(dist, 2),
        "eta_s": eta,
        "threat_level": threat["threat_level"],
        "message": f"{nearest['id']} dispatched — ETA ~{eta}s"
    })


@app.route("/status", methods=["GET"])
def status():
    return jsonify({"interceptors": interceptors, "threats": threats})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
