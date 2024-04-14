from collections import deque
import numpy as np
import cv2
import json

class StateDetector:
    def __init__(self,args):
        
        
        self.threshold = args.state_threshold
        self.moving_treshold = args.moving_threshold
        self.state_stack_lock = False
        self.queue =deque(maxlen=args.max_frames_stack)
        self.imshape=args.imshape
        self.last_frame = np.zeros(self.imshape)
        
    def get_scene_state(self,frame):
        try:
            
            # input is a frame in one chhannell grayscale with 0-255 range
            frame = cv2.resize(frame, self.imshape[::-1])
            
            framescaled=frame/ 255.
            
            self.capture=False
            # calculate score by subtracting background from the max pixel and scaling to 0-1 range
            score = (np.max(framescaled) - np.median(framescaled)) 
            # set difference to previous frame
            
            
            difference =np.linalg.norm(framescaled-self.last_frame) #np.sqrt((framescaled - self.last_frame)**2) #L2
            self.last_frame = framescaled
            
            state = "undecided"
            # deciding wether a frame is empty or moving
            if score < self.threshold:
                state = "empty"
            
            if difference > self.moving_treshold and score > self.threshold:
                state = "moving"
            
            if difference < self.moving_treshold and score > self.threshold:
                state = "still"
            #  push it to the stack FIFO
            self.queue.append(state)
            
            
            # reseting the statelock by having other states in the stack 
            if all(state != "still" for state in self.queue):
                self.state_stack_lock =False
                
            # if all the frames in the stack are still and the state is not locked we can capture the image , indicated by return capture = True
            if all(state == "still" for state in self.queue) and not self.state_stack_lock:
                self.state_stack_lock = True
                self.capture = True
                state = "empty"
                return state , self.capture
            
            
            # retrun the state and the indicator for capturing the image
            return state , self.capture
        except Exception as e:
            print(e)
            return "undecided" , False
