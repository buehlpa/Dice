
import utils.threading_utils as tu
from utils.state_predictor import StateDetector
from io import BytesIO
import cv2
from flask import Flask, Response, request, render_template_string,send_file
import webbrowser
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
import threading
import os
import logging
log = logging.getLogger('werkzeug')
log.disabled = True
import matplotlib
matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()


RESPATH= r'C:\Users\buehl\repos\Dice\rasperry_run\results'


def append_to_csv(path, dice_sum):
    csv_file = os.path.join(path, 'res.csv')
    df = pd.DataFrame({'Numbers': [dice_sum]})
    # If the file does not exist, create it with header, else append without header
    if not os.path.isfile(csv_file):
        df.to_csv(csv_file, mode='w', header=True, index=False)
    else:
        df.to_csv(csv_file, mode='a', header=False, index=False)



# camerastream + models 
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
            append_to_csv(RESPATH, dice_sum)
            
        
        
        # ov    
        cv2.putText(frame, show_state, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, show_dice, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

        
        
        
        
        
        # send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        displayframe = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + displayframe + b'\r\n')

def plot_histogram(data_path, column_name):
    with matplotlib_lock:
        df = pd.read_csv(data_path)
        plt.figure()
        df[column_name].hist()
        
        plt.title(f'Histogram of {column_name}')
        plt.xlabel(column_name)
        plt.ylabel('Frequency')
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img





#http://127.0.0.1:5000/plot.png

app = Flask(__name__)

@app.route('/reset_histogram', methods=['POST'])
def reset_histogram():
    csv_file = os.path.join(RESPATH, 'res.csv')
    # Reset the file by writing only the header
    with open(csv_file, 'w') as file:
        file.write('Numbers\n')
    return '', 204  # Return no content status


@app.route('/plot.png')
def plot_png():
    data_path = r'C:\Users\buehl\repos\Dice\rasperry_run\results\res.csv'  # Replace with your CSV file path
    column_name = 'Numbers'         # Replace with the column name
    img = plot_histogram(data_path, column_name)
    return send_file(img, mimetype='image/png')


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

# TODO make UI nicer
# TODO proper histogramm
# CSS fonts for zhaw helvitca rounded bold 
# TODO IDP LOGO inverse weisse scrhirt auf blauem hintergrund oder transpartent , sowie zhaw.ch
# BUG closing the app does not stop all processes , fix 
@app.route('/')
def index():
    return render_template_string("""<html>
<head>
    <title>Dice Detection System</title>
    <link rel="icon" href="{{ url_for('static', filename='logo.ico') }}" type="image/x-icon">

    <style>
    @font-face {
    font-family: 'Helvetica Rounded Bold';
    src: url('helvetica-rounded-bold.woff2') format('woff2'),
         url('helvetica-rounded-bold.woff') format('woff');
    font-weight: bold;
    font-style: normal;
}
    
    
    
        body {
            font-family: 'Helvetica Rounded Bold', Arial, sans-serif;
            background-color: white;
            color: #333;
            margin: 0;
            padding: 0;
        }
        .header {
            background-color: #0165A8;
            color: white;
            padding: 10px;
            text-align: center;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .header h1 {
            margin: 0;
        }
        .footer {
            background-color: #0165A8;
            color: white;
            padding: 10px;
            text-align: right;
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            box-shadow: 0 -2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }
        .footer img {
            max-height: 100px;
        }
        .content {
            margin: 20px;
            display: flex;
            justify-content: space-around;
            padding-top: 60px; /* Space for the fixed header */
            padding-bottom: 60px; /* Space for the fixed footer */
        }
        .box {
            border: 2px solid #0073e6;
            margin-bottom: 20px;
            text-align: center;
            width: 45%;
        }
        .box img {
            max-width: 100%;
            height: auto;
        }
        .fixed-size {
            height: 700px;
            overflow: hidden;
        }
    </style>
    
</head>
<body>
    <div class="header">
        <h1>Dice Detection System</h1>
    </div>
    <div class="content">
        <div class="box fixed-size">
            <h2>Camera Stream</h2>
            <img src="/video_feed" alt="Camera Stream">
        </div>
        <div class="box fixed-size">
            <h2>Histogram</h2>
            <img id="histogram" src="/plot.png" alt="Histogram">
            <button onclick="resetHistogram()">Reset Histogram</button>
        </div>
    </div>
    <div class="footer">
        <img src="static/ZHAW_IDP.jpg" alt="IDP-Logo">
    </div>
    <script>
        function refreshImage() {
            var img = document.getElementById("histogram");
            var newSrc = "/plot.png?random=" + Math.random();
            img.src = newSrc;
        }
        setInterval(refreshImage, 1000); // Refresh every 1000 milliseconds (1 second)
        window.onbeforeunload = function() {
            navigator.sendBeacon('/close_app');
        }
            function resetHistogram() {
        fetch('/reset_histogram', { method: 'POST' })
        .then(response => {
            if (response.ok) {
                console.log("Histogram reset successfully.");
                refreshImage(); // Refresh the histogram image
            }
        })
        .catch(error => console.error('Error:', error));
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