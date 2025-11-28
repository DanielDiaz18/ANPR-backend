from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import cv2
import time
import io
import app.deteccion.engine as engine 

router = APIRouter()

def generate_frames():
    while True:
        # Se usa engine.frame_lock y engine.output_frame
        with engine.frame_lock:

            if engine.output_frame is None:
                time.sleep(0.1)
                continue
            
            # Se codifica a JPEG
            (flag, encoded_image) = cv2.imencode(".jpg", engine.output_frame)
            if not flag:
                continue
            
            frame_bytes = io.BytesIO(encoded_image).read()

        # Yield del frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        #Nota: Es funcional a .04
        time.sleep(0.01)

@router.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")