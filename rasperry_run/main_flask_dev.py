import cv2
import utils.threading_utils as tu
from utils.state_predictor_classic import StateDetector
from flask import Flask, Response, request


app = Flask(__name__)

global cap

def gen_frames():
    global cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    # TODO add calibration functionality 
    state_detector = StateDetector(threshold=0.1, moving_treshold =10, max_frames_stack=4,imshape=(480, 640))
    
    
    tu.start_workers()

    show_dice = 'Dice:  '
    show_state = 'State: '

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        
        # run fast state detection 
        grayscaleframe= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        state , capture=state_detector.get_scene_state(grayscaleframe)
        show_state = f'State: {state}'
        
        # if state detector returned capture = True, enqueue the frame for dice detection 
        if capture:
            frame_resized = cv2.resize(frame, (224, 224))
            tu.enqueue_frame_for_dice(frame_resized)
            
        # if dice prediction is available, show it    
        dice_prediction = tu.get_dice_prediction()
        if dice_prediction:
            dice_sum, dice_pass = dice_prediction
            show_dice = f'Dice: {dice_sum}'
            
        cv2.putText(frame, show_state, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, show_dice, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        # send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/close_app', methods=['POST'])
def close_app():
    global cap
    if cap.isOpened():
        cap.release()
    cv2.destroyAllWindows()
    tu.stop_workers()


@app.route('/')
def index():
    return """<html>
                <body>
                    <img src="/video_feed">
                    <script type="text/javascript">
                        window.onbeforeunload = function(){
                            navigator.sendBeacon('/close_app');
                        }
                    </script>
                </body>
              </html>"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

