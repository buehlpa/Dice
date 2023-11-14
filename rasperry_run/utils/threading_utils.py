import threading
import queue
import numpy as np
import time
## V1  
#from utils.eyes_predictor import get_sum_in_image
#from utils.state_predictor import predict_state

## V2
from utils.predictors import DiceStatePredictor, DiceRecognizer
dice_Pred=DiceRecognizer()
state_Pred=DiceStatePredictor()




### dummy utils for testing if tensorflowlite does not work  , for testing only els eimpoort from utils
def predict_state(frame):
    time.sleep(0.5)
    return np.choose(1, ["empty", "still", "rolling"])
def get_sum_in_image(frame):
    time.sleep(0.5)
    return np.choose(1, [1,2,3,4,5,6]) , True 










# Queues for frame input and prediction output
state_input_queue = queue.Queue(maxsize=2)
state_output_queue = queue.Queue(maxsize=2)

dice_input_queue = queue.Queue(maxsize=5)
dice_output_queue = queue.Queue(maxsize=5)

def state_worker():
    while True:
        frame = state_input_queue.get()
        if frame is None:  # Exit signal
            break
        try:
            ## V1  
            # class_label_state = predict_state(frame)
            ## V2
            class_label_state = state_Pred.predict_state(frame)  
            
            state_output_queue.put(class_label_state)
        except Exception as e:
            state_output_queue.put(e)

def dice_worker():
    while True:
        frame = dice_input_queue.get()
        if frame is None:  # Exit signal
            break
        try:
            ## V1  
            # dice_predicted_sum, dice_prediction_pass = get_sum_in_image(frame)
            ## V2
            dice_predicted_sum, dice_prediction_pass = dice_Pred.get_sum_in_image(frame)
            
            dice_output_queue.put((dice_predicted_sum, dice_prediction_pass))
        except Exception as e:
            dice_output_queue.put(e)

def start_workers():
    # Start worker threads
    threading.Thread(target=state_worker, daemon=True).start()
    threading.Thread(target=dice_worker, daemon=True).start()

def stop_workers():
    # Signal the worker threads to stop
    state_input_queue.put(None)
    dice_input_queue.put(None)

def enqueue_frame(frame):
    state_input_queue.put(frame)
    dice_input_queue.put(frame)
    
def enqueue_frame_for_state(frame):
    state_input_queue.put(frame)

def enqueue_frame_for_dice(frame):
    dice_input_queue.put(frame)

def get_state_prediction():
    if not state_output_queue.empty():
        return state_output_queue.get()

def get_dice_prediction():
    if not dice_output_queue.empty():
        return dice_output_queue.get()
