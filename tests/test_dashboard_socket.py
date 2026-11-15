"""Integration checks: authorized WebSocket frames, permissions and updated data."""
from datetime import datetime, timezone
from starlette.websockets import WebSocketDisconnect
from app.models import VitalSigns
import dashboard.run  # register WebSocket route on the existing FastAPI app

def test_authorized_websocket_stream(demo):
    pid = demo["patient_id"]
    with demo["client"].websocket_connect("/ws/monitor") as ws:
        ws.send_json({"token":demo["tokens"]["nurse"],"patient_id":pid})
        first = ws.receive_json()
        assert first["patient_id"] == pid
        assert first["latest"] is None
        with demo["session"]() as db:
            db.add(VitalSigns(patient_id=pid,systolic=148,diastolic=91,pulse=81,
                              measured_at=datetime.now(timezone.utc),source="manual"))
            db.commit()
        update = ws.receive_json()
        assert update["latest"]["systolic"] == 148
        assert update["severity"] == "warning"

def test_websocket_denies_unassigned_chart(demo):
    with demo["client"].websocket_connect("/ws/monitor") as ws:
        ws.send_json({"token":demo["tokens"]["nurse"],"patient_id":demo["other_id"]})
        try:
            ws.receive_json()
            assert False, "Unauthorized stream unexpectedly returned data"
        except WebSocketDisconnect as exc:
            assert exc.code == 1008

def test_websocket_denies_invalid_token(demo):
    with demo["client"].websocket_connect("/ws/monitor") as ws:
        ws.send_json({"token":"invalid", "patient_id":demo["patient_id"]})
        try:
            ws.receive_json()
            assert False, "Invalid credentials were accepted"
        except WebSocketDisconnect as exc:
            assert exc.code == 1008
