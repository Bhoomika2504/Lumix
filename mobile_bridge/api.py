from fastapi import FastAPI, WebSocket
import uvicorn
import asyncio
import logging
from pydantic import BaseModel
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MobileBridge")

app = FastAPI(title="LUMIX HUD Bridge")

# Data models for incoming requests
class NavRequest(BaseModel):
    destination: str

class ContactUpdate(BaseModel):
    contacts: List[str]

# Global state reference (to be linked with main.py)
system_state = {
    "speed": 0,
    "battery": 100,
    "active_alert": None,
    "location": {"lat": 18.4575, "lng": 73.8677}, # Example: TCOER, Pune
}

@app.get("/status")
async def get_status():
    """Returns the current helmet vitals to the app."""
    return system_state

@app.post("/navigate")
async def start_navigation(nav: NavRequest):
    """Sets a new destination from the mobile app."""
    logger.info(f"New destination received: {nav.destination}")
    # In main.py, this will trigger the routing logic
    return {"status": "success", "destination": nav.destination}

@app.post("/sos/cancel")
async def cancel_sos():
    """Remotely cancel an SOS countdown from the phone screen."""
    logger.warning("SOS Cancelled via Mobile App")
    return {"status": "sos_aborted"}

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """Live stream of HUD data for the app's dashboard."""
    await websocket.accept()
    try:
        while True:
            # Send live telemetry every second
            await websocket.send_json(system_state)
            await asyncio.sleep(1)
    except Exception as e:
        logger.info(f"App disconnected from stream: {e}")

def run_api():
    """Helper to run the server in a background thread."""
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

if __name__ == "__main__":
    run_api()