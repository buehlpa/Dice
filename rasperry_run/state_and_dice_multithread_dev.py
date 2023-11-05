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

show_state=f'State: "None'
show_dice=f'Dice: "None'

def reset_counters():
    global counterEmpty, counterRolling, counterStill, counterRemoving
    global stateEmpty, stateRolling, stateStill, stateRemoving
    
    counterEmpty = 0
    counterRolling = 0
    counterStill = 0
    counterRemoving = 0
    
    stateEmpty = False
    stateRolling = False
    stateStill = False
    stateRemoving = False

# Global variables for counters
counterEmpty = 0
counterRolling = 0
counterStill = 0
counterRemoving = 0

# Global variables for states
stateEmpty = False
stateRolling = False
stateStill = False
stateRemoving = False

dice_prediction=None

# Main loop
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break

    # Resize the frame to the required input size
    frame_resized = cv2.resize(frame, (224, 224))



    tu.enqueue_frame_for_state(frame_resized)
    
    # Attempt to get predictions and overlay them on the frame
    state_prediction = tu.get_state_prediction()
    
    if state_prediction:
        if stateEmpty==False:
            if counterEmpty<4:
                if state_prediction == "empty":
                    counterEmpty+=1
                else:
                    pass
            if counterEmpty>=4:
                stateEmpty=True
        else:
            pass    
            
        
        if stateRolling==False:
            if counterRolling<4 and stateEmpty==True:
                if state_prediction == "rolling":
                    counterRolling+=1
                else:
                    pass
            if counterRolling>=4:
                stateRolling=True   
        else:
            pass     
        
        
        if stateStill==False:    
            if counterStill<4 and stateRolling==True:
                if state_prediction == "still":
                    counterStill+=1
                else:
                    pass   
            if counterStill>=4:
                tu.enqueue_frame_for_dice(frame_resized)
                dice_prediction = tu.get_dice_prediction()
                if dice_prediction:
                    dice_sum, dice_pass = dice_prediction
                
                if dice_pass==False:
                    #TODO overlay frame with "oops try again"
                    reset_counters()
                else:
                    print("Dice: ",dice_sum)
                    #TODO write to df
                    stateStill=True  
        else:
            pass       
        
        if stateRemoving==False:
            if counterRemoving<4    and stateStill==True:
                if state_prediction == "rolling":
                    counterRemoving+=1
                else:
                    pass
            if counterRemoving>=4:
                stateRemoving=True
                reset_counters()
        else:
            pass     
    
    
    
    if state_prediction: 
        show_state=f'State: {state_prediction}'
        
    cv2.putText(frame,show_state , (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

    if dice_prediction: 
        show_state=f'State: {dice_prediction}'

    cv2.putText(frame, show_dice, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)


    # Show the frame
    cv2.imshow('frame', frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Stop the worker threads and release resources
tu.stop_workers()
cap.release()
cv2.destroyAllWindows()
