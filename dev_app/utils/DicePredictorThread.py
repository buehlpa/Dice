
import threading
import queue
import numpy as np
import random

from utils.dice_predictor import * 
# 
# 
# # uncomment on raspebrry pi, comment on locacl machine
#def predict_dice(frame):
#  new=random.choice([1,2,3,4,5,6]) 
 # return new , True 



class DicePredictorThread:
    def __init__(self):
        self.dice_input_queue = queue.Queue(maxsize=5)
        self.dice_output_queue = queue.Queue(maxsize=5)
        # You may include any additional initialization as needed.

    def dice_worker(self):
        while True:
            frame = self.dice_input_queue.get()
            if frame is None:  # Exit signal
                break
            try:
                dice_predicted_sum, dice_prediction_pass = predict_dice(frame)
                self.dice_output_queue.put((dice_predicted_sum, dice_prediction_pass))
            except Exception as e:
                print(f"An error occurred in dice_worker: {e}")
                self.dice_output_queue.put(e)

    def start_workers(self):
        # Start worker thread
        threading.Thread(target=self.dice_worker, daemon=True).start()

    def stop_workers(self):
        # Signal the worker threads to stop
        self.dice_input_queue.put(None)

    def enqueue_frame(self, frame):
        self.dice_input_queue.put(frame)
        
    def enqueue_frame_for_dice(self, frame):
        self.dice_input_queue.put(frame)

    def get_dice_prediction(self):
        if not self.dice_output_queue.empty():
            return self.dice_output_queue.get()

    # Add other methods as required, potentially from the eyes_predictor file.
