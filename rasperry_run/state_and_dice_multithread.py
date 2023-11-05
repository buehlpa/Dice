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



# Main loop
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Resize the frame to the required input size
    frame_resized = cv2.resize(frame, (224, 224))


    tu.enqueue_frame_for_dice(frame_resized)
    # Attempt to get predictions and overlay them on the frame
    state_prediction = tu.get_state_prediction()
    
    
    
    if state_prediction:
        cv2.putText(frame, f'State: {state_prediction}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)




    tu.enqueue_frame_for_state(frame_resized)
    dice_prediction = tu.get_dice_prediction()
    
    if dice_prediction:
        dice_sum, dice_pass = dice_prediction
        cv2.putText(frame, f'Dice: {dice_sum}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)




    # Update the condition variables as needed, based on your application logic

    # Show the frame
    cv2.imshow('frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the worker threads and release resources
tu.stop_workers()
cap.release()
cv2.destroyAllWindows()
