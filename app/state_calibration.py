import cv2
import numpy as np
import seaborn as sns
import matplotlib
matplotlib.use('TkAgg')  # Set the backend explicitly
import matplotlib.pyplot as plt
import json


'''
by running this file yopu can determine the threshold to distingusishc still from empty scene
'''



def calibrate_state(calibration_file="configuration/config.json"):
    print("Calibration process started , wait for camera window to show & follow the instructions there...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_EXPOSURE, 50)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    
    imshape=(480,640)
    images=[]
    images_captured = 0
    
    capture_dict={0:"one white die",
                1:"two white dice",
                2:"one red die",
                3:"two red dice",
                4:"one red die and one white die",
                5:"two red dice and 2 white dice",
                6:"empty scene",
                7:"empty scene again",
                8:"empty scene .. again ",
                9:"empty scene .. last one!"}
     
    while images_captured < 10:
        _, frame = cap.read()
        
        frame = cv2.resize(frame, imshape[::-1])
        
        grayscaleframe= cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        txt_instructions="Press SPACE to capture image with: "
        capture_type = f"{capture_dict[images_captured]}"
        cv2.putText(frame, txt_instructions, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(frame, capture_type, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.imshow('frame', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            images.append(grayscaleframe)
            images_captured += 1
            print("Image captured")
        elif key == ord('q'):
            print("Exiting program.")
            break
        
    cap.release()
    cv2.destroyAllWindows()
    
    if images_captured == 10:
        scores =[(np.max(im )-np.median(im))/255 for im in images]
        labels = ['dice', 'empty']
        colors = ['blue', 'orange']
        sns.histplot(scores[:-4], kde=True, color=colors[0], label=labels[0], alpha=0.5)
        sns.histplot(scores[-4:], kde=True, color=colors[1], label=labels[1], alpha=0.5)
        plt.xlabel('Scores')
        plt.ylabel('Frequency')
        plt.legend()
        plt.show(block=False)
    print("Now you should see a histogram with two distributions, pick a threshold between them to distinguish between empty scene and scene with dices.")
    new_threshold = float(input(r"Enter threshold as float in the terminal:"))
    print("New threshold:", new_threshold)
    
    confirm = str(input("Save to configuration?: Y/n"))
    if confirm == 'Y':
        with open(calibration_file) as f:
                calibration_dict = json.load(f)
        calibration_dict['state_threshold']=new_threshold
        
        with open(calibration_file, 'w') as f:
            json.dump(calibration_dict, f)
        print("Calibration saved to configuration file.")
        
    plt.close()
    print("Calibration process completed.")
    
if __name__ == "__main__":  
    calibration_file="configuration/state_calibration.json"
    calibrate_state(calibration_file)
