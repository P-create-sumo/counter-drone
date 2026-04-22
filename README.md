# Counter-Drone Interceptor — Command & Control
**Open-source fleet management for autonomous counter-drone interceptors.**

Physical interception happens at the edge (on-drone). This system is the mobile command center: receives YOLOv8 detections, assigns the nearest interceptor, tracks GPS in real-time, and logs every engagement.

## Live Demo
👉 [ares-os-app-7bb72773.base44.app/CounterDroneDemo](https://ares-os-app-7bb72773.base44.app/CounterDroneDemo)

## Architecture
```
YOLOv8 Edge Sensor
        ↓
POST /webhook/threat  (JSON: class, confidence, lat, lon, speed)
        ↓
Counter-Drone C2 (Base44)
  → Haversine nearest-interceptor search
  → Status update: Standby → InFlight
  → GPS tracking: interceptor + threat
  → Engagement log
        ↓
Interceptor drone receives coordinates via telemetry link
        ↓
Physical interception (edge autonomous)
```

## Webhook API

**Endpoint:** `POST /functions/threatWebhook`

```json
{
  "classification": "FPV",
  "confidence": 0.96,
  "lat": 48.375,
  "lon": 31.163,
  "alt_m": 70,
  "speed_kmh": 115,
  "heading_deg": 220,
  "source": "YOLOv8-optical"
}
```

**Response:**
```json
{
  "success": true,
  "threat_id": "THR-LK7X9A",
  "assigned_drone": "INT-002",
  "distance_km": 0.42,
  "eta_s": 18,
  "threat_level": "CRITICAL",
  "message": "INT-002 dispatched"
}
```

## Threat Classification
| Class | Auto-Level | Notes |
|-------|-----------|-------|
| FPV (conf >0.85) | CRITICAL | Immediate dispatch |
| Loitering | HIGH | Loitering munition priority |
| speed >80km/h | HIGH | Fast mover |
| Quadcopter | MEDIUM | Standard ISR |
| Unknown | LOW | Monitor |

## Modules
| Module | Status |
|--------|--------|
| YOLOv8 webhook receiver | ✅ Live |
| Haversine nearest-interceptor | ✅ Live |
| Real-time GPS tracking | ✅ Live |
| Threat registry | ✅ Live |
| Fleet status dashboard | ✅ Live |
| Engagement audit log | ✅ Live |
| Telemetry link (MAVLink) | 🔜 Roadmap |
| Autonomous RTB on neutralization | 🔜 Roadmap |

## License
MIT — free forever
