""""_summary_
Main file to run the flask app.
The app opens a browser window with the camera stream and the results of the dice prediction.
"""


#misc
import time
import cv2
import pandas as pd
import threading

# own utils
from utils.DicePredictorThread import DicePredictorThread
from utils.state_predictor import StateDetector
from utils.results import write_result, plot_histogram
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

#load arguments from configuration file
argpath='configuration/config.json'
global args 
args=load_and_parse_args(argpath)

global use_canny
use_canny=True

# camerastream + models 
def gen_frames():
    global cap
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_EXPOSURE, args.CAP_PROP_EXPOSURE)
    
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    # initiate dice detector and start separate thread
    dice_detector=DicePredictorThread()
    dice_detector.start_workers()
    
    # IF you want to calibrate camera run separate calibration script 
    # initiate state detector  
    state_detector = StateDetector(args)
    
    if args.DEBUG_MODE:
        #for fps calculation
        frame_count = 0
        start_time = time.time()
        fps = 1
    
    # initiate states for overlay on image
    dice_msg = 'Warte auf Vorhersage ... '
    state_msg = 'Initialisiere .. Status '    
    
    # frame loop 
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            cap.release()
            break
        
        # cut the lowest part of the image
        frame= frame[:args.frame_cut_x,:,:]

        # run fast state detection 
        grayscaleframe= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        state , capture=state_detector.get_scene_state(grayscaleframe)
        state_msg = f'{args.msg[state]}'
        
        # if state detector returned capture = True, enqueue the frame for dice detection 
        if capture:
            frame_resized = cv2.resize(frame, (224, 224))
            dice_detector.enqueue_frame_for_dice(frame_resized)
            
        # if dice prediction is available, show it    
        dice_prediction = dice_detector.get_dice_prediction()
                
        
        if dice_prediction:
            dice_msg= write_result(dice_prediction, filepath=os.path.join(args.RESPATH,'results.csv'))
        
        if args.DEBUG_MODE:
            print(f'state:{state}',f'capture:{capture}',f'dice_prediction:{dice_prediction}')
            # Calculate and display FPS
            frame_count += 1
            elapsed_time = time.time() - start_time
            if elapsed_time >= 1.0:  # Update FPS every second
                fps = int(frame_count / elapsed_time)
                frame_count = 0
                start_time = time.time()
                
        if use_canny:    
            frame =cv2.Canny(frame,150,200)   
    
        # overlay state, dicecount and  FPS on the frame
        cv2.putText(frame, state_msg, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, dice_msg, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)
        
        if args.DEBUG_MODE:
            cv2.putText(frame, f'FPS: {fps:.2f}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA) 
            
        #send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        displayframe = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + displayframe + b'\r\n')


####### app routing
app = Flask(__name__)

# Routes
@app.route('/reset_histogram', methods=['POST'])
def reset_histogram():
    '''resets results file to an empty csv'''
    csv_file = os.path.join(args.RESPATH, 'results.csv')
    results={"throw":[],"white":[],"red":[]}
    df = pd.DataFrame(results)
    df.to_csv(csv_file, index=False)
    print("reset")
    return '', 204  # Return no content status

@app.route('/plot.png')
def plot_png():
    data_path = os.path.join(args.RESPATH, 'results.csv')     
    img = plot_histogram(data_path)
    return send_file(img, mimetype='image/png')


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

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

# Route to toggle use_canny variable
@app.route('/toggle_canny', methods=['POST'])
def toggle_canny():
    global use_canny
    use_canny = not use_canny
    if args.DEBUG_MODE:
        print("use_canny set to:", use_canny)
    return '', 204  # Return no content status

# Main route , load html
@app.route('/')
def index():
    with open(os.path.join(args.PAGE_PATH,'page.html'), 'r') as file:
        page_content = file.read()
    return render_template_string(page_content)

#automatically open browser
def open_browser():
     webbrowser.open_new('http://127.0.0.1:5000/')

if __name__ == '__main__':
    threading.Timer(0.5, open_browser).start()
    app.run(host='0.0.0.0', port=5000)
