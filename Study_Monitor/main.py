import cv2
import numpy as np
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from study_monitor import StudyMonitor

app = FastAPI(title="Mishka Vision ML Processing Service")

# Essential to allow connection channels from mobile devices safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Mishka ML WebSocket Service is active on port 8000!"}

@app.get("/health")
def health_check():
    return {"ok": True, "service": "study-monitor"}

def sync_frame_processing(bytes_data, monitor_instance):
    """
    Executes synchronous, high-frequency image array compilation 
    safely isolated from your main asynchronous event router loop.
    """
    nparr = np.frombuffer(bytes_data, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if frame is None:
        return None
        
    _, status, _ = monitor_instance.process_frame(frame)
    return status

@app.websocket("/ws/study-session")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🚀 Flutter client handshake accepted over WebSocket!")
    
    # Instance created specifically per connection session
    monitor = StudyMonitor()
    
    try:
        while True:
            # Receive raw binary image data (JPEG bytes) from mobile app
            bytes_data = await websocket.receive_bytes()
            
            # Offload heavy CPU calculation to a worker thread to prevent blocking
            status = await asyncio.to_thread(sync_frame_processing, bytes_data, monitor)
            
            if status is None:
                continue
                
            # Send back the response status text string
            await websocket.send_json({"status": status})
            
    except WebSocketDisconnect:
        print("❌ Flutter client disconnected gracefully.")
    except Exception as e:
        print(f"Session closed via unexpected interaction: {e}")
    finally:
        # Guarantee unmanaged MediaPipe memory release on disconnect
        monitor.close()
        try:
            await websocket.close()
        except Exception:
            pass