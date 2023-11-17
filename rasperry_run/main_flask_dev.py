import cv2
import utils.threading_utils as tu
from utils.state_predictor_classic import StateDetector
from flask import Flask, Response, request, render_template_string
import webbrowser
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import threading
import os

import matplotlib
matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()


RESPATH= r'C:\Users\buehl\repos\Dice\rasperry_run\results'

# camerastream + models 
def gen_frames():
    global cap
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    # TODO add calibration functionality 
    state_detector = StateDetector(threshold=0.1, moving_treshold =10, max_frames_stack=4,imshape=(480, 640))
    
    
    tu.start_workers()# Todo

    show_dice = 'Dice:  '
    show_state = 'State: '

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            cap.release()
            tu.stop_workers()
            cv2.destroyAllWindows()
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

# BUG does not display any image just placeholder
def plot_histogram():
    with matplotlib_lock:
        try:
            df = pd.read_csv(os.path.join(RESPATH, 'res.csv'), header=None)
            plt.hist(df[0])
            plt.title('Histogram')
            plt.xlabel('Values')
            plt.ylabel('Frequency')
        except Exception as e:
            print(e)
            # Load your error image here instead
            plt.text(0.5, 0.5, 'Error in generating histogram', horizontalalignment='center', verticalalignment='center')
            # If you have a specific error image, load and use it here

        # This part executes whether or not there was an exception
        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()
        plt.close()
        return f'data:image/png;base64,{plot_url}'



#http://127.0.0.1:5000/plot.png

app = Flask(__name__)

# BUG does not display any image just placeholder
@app.route('/plot.png')
def plot_png():
    plot_url = plot_histogram()
    return Response(plot_url, mimetype='image/png')


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
    return render_template_string("""<html>
                <body>
                    <img src="/video_feed">
                    <img id="histogram" src="/plot.png">
                    <script>
                    setInterval(function(){document.getElementById('histogram').src = '/plot.png';}, 2000);
                        
                        window.onbeforeunload = function(){
                            navigator.sendBeacon('/close_app');
                        }
                    </script>
                </body>
              </html>""")
              
              
              
              
#automatically open browser
def open_browser():
      webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(0.5, open_browser).start()
    app.run(host='0.0.0.0', port=5000)