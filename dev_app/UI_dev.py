
######################################


# THIS FILE DOES NOT CONTAIN THE PREDCITION MODEL
## JUst use thios for UI DEV

####################################

#misc
import time
import cv2
import pandas as pd
import threading

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


# DEBUG MODE
DEBUG_MODE=True


#load arguments from configuration file
# on windows : r'C:\Users\buehl\repos\Dice\rasperry_run\configuration\config_win.json'
#argpath= 'configuration/config.json'
argpath= r'C:\Users\buehl\repos\Dice\dev_app\configuration\config_win.json'

#argpath=r'C:\Users\buehl\repos\Dice\rasperry_run\configuration\config_win.json' #
global args 
args=load_and_parse_args(argpath)

global use_canny
use_canny = False

print(args)
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
    column_name = 'red'      
    img = plot_histogram(data_path, column_name)
    return send_file(img, mimetype='image/png')

@app.route('/plot2.png')
def plot2_png():
    data_path = os.path.join(args.RESPATH, 'results.csv')  
    column_name = 'white'         
    img = plot_histogram(data_path, column_name)
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
    
    print("use_canny set to:", use_canny)
    if DEBUG_MODE:
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
