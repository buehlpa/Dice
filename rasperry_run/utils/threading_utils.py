import threading
import queue
from utils.eyes_predictor import get_sum_in_image
from utils.state_predictor import predict_state

# Queues for frame input and prediction output
state_input_queue = queue.Queue()
state_output_queue = queue.Queue()
dice_input_queue = queue.Queue()
dice_output_queue = queue.Queue()

def state_worker():
    while True:
        frame = state_input_queue.get()
        if frame is None:  # Exit signal
            break
        try:
            class_label_state = predict_state(frame)
            state_output_queue.put(class_label_state)
        except Exception as e:
            state_output_queue.put(e)

def dice_worker():
    while True:
        frame = dice_input_queue.get()
        if frame is None:  # Exit signal
            break
        try:
            dice_predicted_sum, dice_prediction_pass = get_sum_in_image(frame)
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
