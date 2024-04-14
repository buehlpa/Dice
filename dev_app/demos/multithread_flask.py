from flask import Flask, Response
import cv2
import threading

app = Flask(__name__)

# Initialize video capture
cap = cv2.VideoCapture(0)

# Shared data structure for frame handling
frame_lock = threading.Lock()
current_frame = None
processed_frame = None

def capture_frames():
    global current_frame
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        with frame_lock:
            current_frame = frame.copy()

def process_frames():
    global processed_frame
    while True:
        with frame_lock:
            if current_frame is not None:
                # Perform some heavy processing here
                # For example, let's just convert the frame to grayscale
                processed_frame = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)

def generate():
    global processed_frame
    while True:
        with frame_lock:
            if processed_frame is not None:
                ret, jpeg = cv2.imencode('.jpg', processed_frame)
                frame = jpeg.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Start the frame capture thread
    threading.Thread(target=capture_frames, daemon=True).start()
    # Start the frame processing thread
    threading.Thread(target=process_frames, daemon=True).start()
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)
