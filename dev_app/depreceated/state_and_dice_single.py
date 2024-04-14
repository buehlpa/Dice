### all togehter export to rasperry pi
from utils.eyes_predictor import get_sum_in_image
from utils.state_predictor import predict_state

import cv2
import numpy as np


# Define class labels for the first and second models
# class_labels_state = ["empty", "rolling", "still"]
# class_labels_dice = ["1", "2", "3", "4", "5", "6"]



# Open a handle to the default webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Convert the frame to RGB, then resize and preprocess it
    frame_resized = cv2.resize(frame, (224, 224))  
    
    
    # Predict the state of the scene
    class_label_state=predict_state(frame_resized)

	# get the number of eyes in the image
    dice_predicted_sum , dice_prediction_pass = get_sum_in_image(frame_resized)  # TODO exception handling with prediciton state = False -> smthn wrong rethrow dices
    print(dice_prediction_pass)
	# Display the resulting frame with the class label
    cv2.putText(frame, f'State: {class_label_state}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
    if dice_predicted_sum:
        cv2.putText(frame, f'Dice: {dice_predicted_sum}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow('frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) == ord('q'):
        break

# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()

