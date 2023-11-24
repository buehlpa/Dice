
import utils.threading_utils as tu
import time
import cv2
from utils.state_predictor import StateDetector
from flask_utils import append_to_csv


RESPATH= 'results'
STATPATH= 'static'



def gen_frames():
    global cap
    cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    
    
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    # TODO add calibration functionality 
    state_detector = StateDetector(threshold=0.1, moving_treshold =10, max_frames_stack=4,imshape=(480, 640))
    
    # start the workes , either multiprocessing or threading
    tu.start_workers()
    
    #for fps calculation

    frame_count = 0
    start_time = time.time()
    fps = 1
    # initiate states
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
            # TODO in the dice predicition function, save the image of the cutted dice ->> show it in an image box
            dice_sum, dice_pass = dice_prediction
            
            if dice_pass:
                show_dice = f'Dice: {dice_sum}'
                append_to_csv(RESPATH, dice_sum)
            else:
                # TODO add a check if the dice pass is true, if not, SHOW : INVALID THROW, Please try again!
                show_dice = f'Dice: {dice_sum}'
                append_to_csv(RESPATH, dice_sum)
        
        # overlay state and dice
        cv2.putText(frame, show_state, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, show_dice, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        
        
        # Calculate and display FPS
        frame_count += 1
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        if elapsed_time >= 1.0:  # Update FPS every second
            fps = int(frame_count / elapsed_time)
            frame_count = 0
            start_time = time.time()
            
        # Display FPS on the frame
        cv2.putText(frame, f'FPS: {fps:.2f}', (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        #send image to flask app
        _, buffer = cv2.imencode('.jpg', frame)
        displayframe = buffer.tobytes()
        yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + displayframe + b'\r\n')