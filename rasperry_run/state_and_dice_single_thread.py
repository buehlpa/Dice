from utils.eyes_predictor import get_sum_in_image
from utils.state_predictor import predict_state
import cv2
import numpy as np
import threading
import queue

# Define queues for frame input and prediction output
state_input_queue = queue.Queue()
state_output_queue = queue.Queue()
dice_input_queue = queue.Queue()
dice_output_queue = queue.Queue()

# Worker thread function for state prediction
def state_worker():
    while True:
        frame = state_input_queue.get()  # Wait until a frame is available
        try:
            class_label_state = predict_state(frame)
            state_output_queue.put(class_label_state)
        except Exception as e:
            state_output_queue.put(e)

# Worker thread function for dice sum prediction
def dice_worker():
    while True:
        frame = dice_input_queue.get()  # Wait until a frame is available
        try:
            dice_predicted_sum, dice_prediction_pass = get_sum_in_image(frame)
            dice_output_queue.put((dice_predicted_sum, dice_prediction_pass))
        except Exception as e:
            dice_output_queue.put(e)

# Start worker threads
state_thread = threading.Thread(target=state_worker, daemon=True)
state_thread.start()
dice_thread = threading.Thread(target=dice_worker, daemon=True)
dice_thread.start()

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Main loop
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Resize the frame to the required input size
    frame_resized = cv2.resize(frame, (224, 224))

    # Put the frame in both input queues for processing
    state_input_queue.put(frame_resized)
    dice_input_queue.put(frame_resized)

    # Check if there are results in the output queues and update accordingly
    if not state_output_queue.empty():
        state_result = state_output_queue.get()
        if not isinstance(state_result, Exception):
            cv2.putText(frame, f'State: {state_result}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    
    if not dice_output_queue.empty():
        dice_result = dice_output_queue.get()
        if not isinstance(dice_result, Exception):
            dice_sum, dice_pass = dice_result
            if dice_pass:
                cv2.putText(frame, f'Dice: {dice_sum}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Show the frame
    cv2.imshow('frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and destroy all windows when done
cap.release()
cv2.destroyAllWindows()
