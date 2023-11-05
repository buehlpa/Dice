# main.py

import cv2
import utils.threading_utils as tu

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Start the worker threads
tu.start_workers()

show_dice='Dice:  '
show_state='State: '

# Main loop
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Resize the frame to the required input size
    frame_resized = cv2.resize(frame, (224, 224))

    # State prediciton
    tu.enqueue_frame_for_state(frame_resized)
    state_prediction = tu.get_state_prediction()
    if state_prediction:
        show_state=f'State: {state_prediction}'
        
    # dice eyes prediciton
    tu.enqueue_frame_for_dice(frame_resized)
    dice_prediction = tu.get_dice_prediction()
    if dice_prediction:
        dice_sum, dice_pass = dice_prediction
        show_dice = f'Dice: {dice_sum}'
 
 
    # Update text
    cv2.putText(frame, show_state, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)       
    cv2.putText(frame,show_dice , (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    # Show the frame
    cv2.imshow('frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord(' '):
        print("hey")


    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the worker threads and release resources
tu.stop_workers()
cap.release()
cv2.destroyAllWindows()
