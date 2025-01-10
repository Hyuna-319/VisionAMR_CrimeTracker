from flask import Flask, Response, render_template
import cv2
import numpy as np
import pyautogui
from threading import Thread
import time

app = Flask(__name__)
# Global variable to store the latest frame
frame = None
stop_thread = False

def capture_rviz():
    global frame, stop_thread
    while not stop_thread:
        # Capture the RViz2 window - you'll need to adjust these coordinates
        # based on your screen and RViz2 window position
        screenshot = pyautogui.screenshot(region=(0, 0, 800, 600))
        # Convert the screenshot to numpy array
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        time.sleep(0.033)  # ~30 FPS
        
def generate_frames():
    global frame
    while True:
        if frame is not None:
            # Encode the frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            # Yield the frame in proper format for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)
        
@app.route('/')

def index():
    return render_template('index.html')
@app.route('/video_feed')

def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
                    
if __name__ == '__main__':
    # Start the capture thread
    capture_thread = Thread(target=capture_rviz)
    capture_thread.start()
    try:
        app.run(host='0.0.0.0', port=8000, debug=False)
    finally:
        # Cleanup when the Flask app is stopped
        stop_thread = True
        capture_thread.join()
