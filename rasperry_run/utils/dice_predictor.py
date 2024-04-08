import numpy as np
import cv2
import random
import os

import tflite_runtime.interpreter as tflite


# Tensorflow lite model directory
model_dir = 'models'
model_file = 'model_single_dices.tflite'
MODEL_PATH = os.path.join(model_dir, model_file)

# Output classes
class_labels_dice = ["1", "2", "3", "4", "5", "6"]


##Load the TFLite model and allocate tensors.
# dice interpreter model detects the number of eyes on the dice
interpreter_dice = tflite.Interpreter(model_path=MODEL_PATH)
interpreter_dice.allocate_tensors()
input_details_dice = interpreter_dice.get_input_details()
output_details_dice = interpreter_dice.get_output_details()
input_shape_dice = input_details_dice[0]['shape']



## Helper functions
def remove_range(hsv_img,low,high):
    '''
    removes a certain range of values on an image and retruns rgb image
    img:hsv image
    low:lower bound e.g. [0,0,0]
    high:higher bound e.g. [255,255,255]
    '''
    bg_mask = cv2.inRange(hsv_img, low, high)
    dices_mask = cv2.bitwise_not(bg_mask)
    img=cv2.cvtColor(hsv_img, cv2.COLOR_HSV2RGB)
    return cv2.bitwise_and(img, img, mask=dices_mask)


def get_cropped(orig_gray,img):
    '''
    returns cropped images of the dices
    img:rgb image
    orig_gray:gray image orignal to crop from 
    '''
    gray_img=cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(gray_img, connectivity=8)
    output_image = np.zeros_like(gray_img)
    for i in range(1, num_labels):  # Start from 1 to ignore the background component
        if stats[i, cv2.CC_STAT_AREA] >= 50:
            output_image[labels == i] = 255  # Keep this connected component
    binary_mask = np.uint8(output_image > 0)
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cropped = []
    hull_mask = np.zeros_like(binary_mask)
    # Loop over each contour
    for contour in contours:
        hull = cv2.convexHull(contour)
        cv2.drawContours(hull_mask, [hull], -1, (255), thickness=cv2.FILLED)
        x, y, w, h = cv2.boundingRect(hull)
        orig_gray_i=orig_gray.copy()
        orig_gray_i[hull_mask==0]=0
        cropped_image = orig_gray_i[y:y+h, x:x+w]
        cropped.append(cropped_image)
    return cropped , hull_mask


def get_white_red(img):
    '''
    img: opencv bgr array 
    
    returns: list of cropped red and white dice images in grayscale
    '''
    # Original imag to grayscale and hsv
    orig_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv_image = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # remove background -> white and red, only take the red ones
    rgb_nogreen=   remove_range(hsv_image,np.array([40, 0, 0]),np.array([90, 255, 255])) #rbg
    rgb_red = remove_range(cv2.cvtColor(rgb_nogreen, cv2.COLOR_RGB2HSV), np.array([30, 0, 0]), np.array([160, 255, 255]))
    
    # get cropped images for red  and the mask of the red die
    cropped_img_red , hull_mask_red =get_cropped(orig_gray,rgb_red)

    # remove red dice from the image
    rgb_nored = rgb_nogreen.copy()  
    rgb_nored[hull_mask_red == 255] = 0

    cropped_img_white, _ = get_cropped(orig_gray,rgb_nored)

    return cropped_img_red,cropped_img_white


def model_dummy(img)-> int:
    '''
    dummy model that returns the number of red and white dices
    mimics:  model.predict(img)
    '''
    return random.randint(1, 6)


def rerun_criterion(img_list:list)-> bool:
    '''
    img_list: list of opencv one channel images
    returns: bool , True if criterion met else False
    '''
    criterion=True
    for img in img_list:
            if  ((img.shape[0] / img.shape[1]) > 1.4) or ((img.shape[1] / img.shape[0]) >  1.4):
                criterion = False
    return criterion



def predict_one_dice(frame:np.array)-> np.array:
    """
    Predicts the number of eyes on a dice in a given frame using a pre-trained TensorFlow Lite model.

    Args:
        frame: A numpy array representing the image frame. shape (w,h)

    Returns:
        A numpy array representing the outcome distribution of the model.
    """
    # Convert frame to grayscale if not already done
    if len(frame.shape) > 2 and frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Resize the image to match the input shape expected by the model
    frame = cv2.resize(frame, (input_shape_dice[1], input_shape_dice[2]))

    # Convert the image to float32
    frame = frame.astype(np.float32)
    
    # Normalize the image if required 
    if frame.max() > 1:
        frame /= 255.0

    # Add a channels dimension
    frame = np.expand_dims(frame, axis=-1)

    # Expand dimensions to represent batch size
    input_data = np.expand_dims(frame, axis=0)
    
    # Set the input tensor
    interpreter_dice.set_tensor(input_details_dice[0]['index'], input_data)
    
    # Run inference
    interpreter_dice.invoke()
    
    # Get the output tensorexit()
    
    output_data_dice = interpreter_dice.get_tensor(output_details_dice[0]['index'])
    return output_data_dice



# Main funciton to predict the number of red and white dices

def predict_dice(frame):
    '''
    img: opencv bgr array 
    returns: number of red and white dices, if criterion met bool
    '''
    cropped_img_red,cropped_img_white = get_white_red(frame)
    
    # check criterion
    if not rerun_criterion(cropped_img_red) or not rerun_criterion(cropped_img_white):
        return _ , False    
    
    resdict={"red_dice":[],"white_dice":[]}
    
    for img in cropped_img_red:
        dice_outcome = predict_one_dice(img)
        pred_class=int(np.argmax(dice_outcome))
        resdict["red_dice"].append(pred_class)
    for img in cropped_img_white:
        dice_outcome=predict_one_dice(img)
        pred_class=int(np.argmax(dice_outcome))
        resdict["white_dice"].append(pred_class)  
        
    return resdict, True






