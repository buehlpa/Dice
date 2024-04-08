#misc
import time
import cv2
import pandas as pd
import threading

# own utils
from utils.DicePredictorThread import DicePredictorThread
from utils.state_predictor import StateDetector
from utils.plotting import *


#flask
from io import BytesIO
import os
from flask import Flask, Response, request, render_template_string, send_file
import webbrowser
import signal

# logger
import logging
log = logging.getLogger('werkzeug')
log.disabled = True

# plotting
from scipy.stats import chisquare
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
import matplotlib# lock matqplotlib for multithreading
matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()

# DEBUG MODE
DEBUG_MODE=True


# PATHS
RESPATH= 'results'#C:\Users\buehl\repos\Dice\rasperry_run\
STATPATH= 'static'


### append to results file
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
    cap.set(cv2.CAP_PROP_EXPOSURE, 50)
    
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    # initiate dice detector and start separate thread
    dice_detector=DicePredictorThread()
    dice_detector.start_workers()
    
    # IF you want to calibrate camera run separate calibration script 
    # initiate state detector  
    state_detector = StateDetector(calibration_file='configuration/state_calibration.json', max_frames_stack=4,imshape=(480, 640))
    

    #for fps calculation
    frame_count = 0
    start_time = time.time()
    fps = 1
    
    # initiate states for overlay on image
    dice_msg = 'Dice:  '
    show_state = 'State: '
    
    # frame loop 
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            cap.release()
            break
        
        # cut the lowest part
        frame= frame[:470,:]
        
        # run fast state detection 
        grayscaleframe= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        state , capture=state_detector.get_scene_state(grayscaleframe)
        show_state = f'State: {state}'
        
        # if state detector returned capture = True, enqueue the frame for dice detection 
        if capture:
            frame_resized = cv2.resize(frame, (224, 224))
            dice_detector.enqueue_frame_for_dice(frame_resized)
            
        # if dice prediction is available, show it    
        dice_prediction = dice_detector.get_dice_prediction()
        
        if DEBUG_MODE:
            print(f'state:{state}',f'capture:{capture}',f'dice_prediction:{dice_prediction}')
        
        if dice_prediction:
            dice_msg= write_result(dice_prediction, filepath='result/results.csv')
        
        # Calculate and display FPS
        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time >= 1.0:  # Update FPS every second
            fps = int(frame_count / elapsed_time)
            frame_count = 0
            start_time = time.time()
            
    
        # overlay state, dicecount and  FPS on the frame
        cv2.putText(frame, show_state, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, dice_msg, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        #cv2.putText(frame, f'FPS: {fps:.2f}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
                
        #send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        displayframe = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + displayframe + b'\r\n')



# helper function to place image on histogarmmplot
def place_image(ax, img_path, xy, zoom=1):
    # Load the image
    img = plt.imread(img_path)
    # Create an OffsetImage
    imagebox = OffsetImage(img, zoom=zoom)
    # Create an AnnotationBbox
    ab = AnnotationBbox(imagebox, xy, frameon=True, xybox=(10, -15), boxcoords="offset points", pad=0)
    # Add it to the axes
    ax.add_artist(ab)


# plot histogram
def plot_histogram(data_path, column_name):
    
    # TODO error thrown when flaots in csv -> handle
    with matplotlib_lock:
        df = pd.read_csv(data_path)
    
        rolls=df[column_name].dropna().tolist()
        # Theoretical distribution for a fair dice (uniform distribution)
        fair_probs = [1/6] * 6  # Since each outcome (1-6) has an equal probability
        
        if len(rolls) != 0:
            # Counting the frequency of each outcome for the unfair dice
            unfair_probs = [rolls.count(i) / len(rolls) for i in range(1, 7)]
            observed_frequencies = [rolls.count(i) for i in range(1, 7)]
            expected_frequencies = [len(rolls) / 6] * 6
            chi_squared_stat, p_value = chisquare(observed_frequencies, f_exp=expected_frequencies)
        
        # Create the plot
        fig, ax = plt.subplots()

        # Plotting the bar charts
        ax.bar(range(1, 7), fair_probs, alpha=1, color='#0165A8', label='Theoretisch', width=0.4)
        
        if column_name == 'red':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, color='red', label='Gewürfelt', width=0.4)
        elif column_name == 'white':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, edgecolor='black', color='white', label='Gewürfelt', width=0.4)

        # Remove numerical x-tick labels and place images instead
        ax.set_xticks(range(1, 7))
        ax.set_xticklabels([])  # Remove x-tick labels
        ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks

        for i in range(1, 7):
            place_image(ax, os.path.join(STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)
            
        plt.title(f'Häufigkeiten von Würfelergebnissen, Anzahl Würfe: {len(rolls)} p= {p_value:.3f}')
        plt.legend()
        plt.xlabel('Würfel Augen', labelpad=30)
        plt.ylabel('Relative Häufigkeit')
                

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img

####### app routing
app = Flask(__name__)

@app.route('/reset_histogram', methods=['POST'])
def reset_histogram():
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
            <button onclick="resetHistogram()">Reset Histogram</button>
        </div>
        
        <div class="box video-frame">
            <h2>Second Histogram</h2>
            <img id="histogram2" src="/plot2.png" alt="Second Histogram">
            <button onclick="resetSecondHistogram()">Reset Second Histogram</button>
        </div>
    </div>

    <div class="footer">
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
