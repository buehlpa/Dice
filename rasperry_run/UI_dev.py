
######################################


# THIS FILE DOES NOT CONTAIN THE PREDCITION MODEL
## JUst use thios for UI DEV

####################################


#misc
import time
import cv2
import pandas as pd
import threading

from utils.plotting import write_result, plot_histogram
from utils.argparser import load_and_parse_args


#flask
import os
from flask import Flask, Response, request, render_template_string, send_file
import webbrowser
import signal

# logger
import logging
log = logging.getLogger('werkzeug')
log.disabled = True


# DEBUG MODE
DEBUG_MODE=True

# PATHS
RESPATH= 'results'
STATPATH= 'static'

## on local WIN os
RESPATH=r'C:\Users\buehl\repos\Dice\rasperry_run\results'
STATPATH=r'C:\Users\buehl\repos\Dice\rasperry_run\static'


# camerastream + models 
def gen_frames():
    global cap
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_EXPOSURE, 50)
    
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    #for fps calculation
    frame_count = 0
    start_time = time.time()
    fps = 1

    # frame loop 
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            cap.release()
            break
        
        # cut the lowest part of the image
        frame= frame[:470,:,:]

        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time >= 1.0:  # Update FPS every second
            fps = int(frame_count / elapsed_time)
            frame_count = 0
            start_time = time.time()
            
        cv2.putText(frame, f'FPS: {fps:.2f}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA) 
                
        #send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        displayframe = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + displayframe + b'\r\n')



####### app routing
app = Flask(__name__)

@app.route('/reset_histogram', methods=['POST'])
def reset_histogram():
    '''resets results file to an empty csv'''
    
    csv_file = os.path.join(RESPATH, 'results.csv')
    results={"throw":[],"white":[],"red":[]}
    df = pd.DataFrame(results)
    df.to_csv(csv_file, index=False)
    return '', 204  # Return no content status

@app.route('/plot.png')
def plot_png():
    data_path = os.path.join(RESPATH, 'results.csv')  
    column_name = 'red'      
    img = plot_histogram(data_path, column_name)
    return send_file(img, mimetype='image/png')

@app.route('/plot2.png')
def plot2_png():
    data_path = os.path.join(RESPATH, 'results.csv')  
    column_name = 'white'         
    img = plot_histogram(data_path, column_name,)
    return send_file(img, mimetype='image/png')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/close_app', methods=['POST'])
def close_app():
    global cap
    try:
        if cap.isOpened():
            cap.release()
            
        os.kill(os.getpid(), signal.SIGTERM)
        return "Closed Successfully", 200  # Return a success message with a 200 OK status
    except Exception as e:
        return str(e), 500  # Return the error message with a 500 Internal Server Error status if something goes wrong




# TODO make UI nicer
# TODO proper histogramm
# TODO put flask structure correctly
# CSS fonts for zhaw helvitca rounded bold 

@app.route('/')
def index():
    return render_template_string("""<!DOCTYPE html>
<html>
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
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .header, .footer {
            background-color: #0165A8;
            color: white;
            padding: 10px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }

        .header {
            min-height: 70px;
        }

        .footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            text-align: right;
        }

        .footer img {
            max-height: 100px;
            margin: 5px 10px;
        }

        .content {
            display: flex;
            flex-direction: row;
            justify-content: space-around;
            margin: 10px; /* Margin around content */
            flex-grow: 1;
            overflow: auto;
        }

        .box {
            display: flex;
            justify-content: center;
            flex-direction: column;
            align-items: center;
            border: 2px solid #0165A8;
            margin: 10px; /* Margin around each box */
            text-align: center;
            flex-grow: 1;
        }
        
        .video-frame {
            border: 2px solid #0165A8;
            padding: 10px;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.5);
            border-radius: 15px;
            background-color: white;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .video-frame img {
            border-radius: 10px;  /* Optional: for rounded corners on the video */
        }  
        
        .footer-buttons {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            margin-right: 20px;
        }
        
        .reset-button {
            background-color: #FF5733;
            color: white;
            border: none;
            padding: 12px 24px; /* Increase padding for larger size */
            border-radius: 8px; /* Increase border-radius for rounded corners */
            margin-left: 10px;
            cursor: pointer;
            font-size: 18px; /* Increase font size */
        }

        .reset-button:hover {
            background-color: #E63C0C;
        } 
    </style>
</head>
<body>
    <div class="header">
        <h1>Erkenne den gefälschten Würfel!</h1>
    </div>

    <div class="content">
        <div class="box video-frame">
            <h2>Camera Stream</h2>
            <img src="/video_feed" alt="Camera Stream">
        </div>
        
        <div class="box video-frame">
            <h2>Histogram</h2>
            <img id="histogram" src="/plot.png" alt="Histogram">
        </div>
        
        <div class="box video-frame">
            <h2>Second Histogram</h2>
            <img id="histogram2" src="/plot2.png" alt="Second Histogram">
        </div>
    </div>

    <div class="footer">
        <div class="footer-buttons">
            <button class="reset-button" onclick="resetHistogram()">Neuer Versuch</button>
        </div>
        <img src="{{ url_for('static', filename='ZHAW_IDP_white.png') }}" alt="IDP-Logo">
    </div>

    <script>
        function refreshImage() {
            var img = document.getElementById("histogram");
            var newSrc = "/plot.png?random=" + Math.random();
            img.src = newSrc;
        }
        
        function refreshSecondImage() {
            var img = document.getElementById("histogram2");
            var newSrc = "/plot2.png?random=" + Math.random();
            img.src = newSrc;
        }
        
        setInterval(refreshImage, 1000); // Refresh every 1000 milliseconds
        setInterval(refreshSecondImage, 1000); // Refresh every 1000 milliseconds

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
        
        function resetSecondHistogram() {
            fetch('/reset_second_histogram', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    console.log("Second Histogram reset successfully.");
                    refreshSecondImage(); // Refresh the second histogram image
                }
            })
            .catch(error => console.error('Error:', error));
        }

        window.onbeforeunload = function() {
            navigator.sendBeacon('/close_app');
        }
    </script>
</body>
</html>

""")




#automatically open browser
def open_browser():
      webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(0.5, open_browser).start()
    app.run(host='0.0.0.0', port=5000)
