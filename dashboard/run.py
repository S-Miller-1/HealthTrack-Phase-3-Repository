"""Run both existing protected FastAPI routes and the Dash UI on one origin.

Launch with: python -m uvicorn dashboard.run:app --reload
"""
import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from starlette.middleware.wsgi import WSGIMiddleware
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.security import current_user
from dashboard.monitor import snapshot

@app.websocket("/ws/monitor")
async def monitor_socket(ws: WebSocket, db: Session = Depends(get_db)):
    await ws.accept()
    try:
        # Credentials go in the first WebSocket message, not in URL/query logs.
        hello = await asyncio.wait_for(ws.receive_json(), timeout=10)
        token = hello.get("token")
        patient_id = hello.get("patient_id")
        if not isinstance(token, str) or type(patient_id) is not int:
            await ws.close(code=1008)
            return
        try:
            user = current_user(token=token, db=db)
        except HTTPException:
            await ws.close(code=1008)
            return
        last_payload = None
        while True:
            try:
                user = current_user(token=token, db=db)  # recheck token expiry and account status
                data = snapshot(db, user, patient_id)
                if not data["enrolled"] or not data["consent"]:
                    await ws.close(code=1008)
                    return
            except (HTTPException, ValueError):
                await ws.close(code=1008)
                return
            # Avoid repetitive UI redraws if the stored data is unchanged.
            comparable = {k: v for k, v in data.items() if k != "updated_at"}
            encoded = json.dumps(comparable, sort_keys=True)
            if encoded != last_payload:
                await ws.send_json(data)
                last_payload = encoded
            # Refresh database identity map so external writes become visible.
            db.expire_all()
            await asyncio.sleep(2)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        try:
            await ws.close()
        except Exception:
            pass

from dashboard.ui import dashboard
app.mount("/dashboard", WSGIMiddleware(dashboard.server))
