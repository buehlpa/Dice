import numpy as np
import cv2

import tflite_runtime.interpreter as tflite
import os


model_dir = 'models'
model_file = 'model_single_dices.tflite'

MODEL_PATH = os.path.join(model_dir, model_file)

class_labels_dice = ["1", "2", "3", "4", "5", "6"]


##Load the TFLite model and allocate tensors.
# dice interpreter model detects the number of eyes on the dice
interpreter_dice = tflite.Interpreter(model_path=MODEL_PATH)

interpreter_dice.allocate_tensors()


input_details_dice = interpreter_dice.get_input_details()
output_details_dice = interpreter_dice.get_output_details()
input_shape_dice = input_details_dice[0]['shape']




def process_image(img):
    """
    # algorithm to mask the green background, isolate each dice in an image .

    Args:
        img: A numpy array representing the input image.

    Returns:
        A tuple containing:
        - A numpy array representing the grayscale image of the detected dice.
        - An integer representing the number of dices detected.
        - A list of numpy arrays representing the cropped images of each detected dice.
    """
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # Define the lower and upper bounds for the green color
    lower_bound = np.array([0, 80, 0])
    upper_bound = np.array([170, 255, 255])

    # Create a mask of the green background
    bg_mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

    # Invert the mask to get the mask of the objects
    objects_mask = cv2.bitwise_not(bg_mask)

    # Remove the background from the objects image
    objects_no_bg = cv2.bitwise_and(img, img, mask=objects_mask)

    # Convert the objects image with no background to grayscale
    objects_gray = cv2.cvtColor(objects_no_bg, cv2.COLOR_RGB2GRAY)

    # Connected components to filter out small areas
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(objects_gray, connectivity=8)

    # Create an output image initialized to zero
    output_image = np.zeros_like(objects_gray)

    dicecount=0
    # Filter out small components based on a size threshold
    for i in range(1, num_labels):  # Start from 1 to ignore the background component
        if stats[i, cv2.CC_STAT_AREA] >= 80:
            output_image[labels == i] = 255
            dicecount+=1

    # Create a binary mask from the output image
    binary_mask = np.uint8(output_image > 0)

    # Find contours in the binary mask
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create an empty mask for the convex hulls
    hull_mask = np.zeros_like(binary_mask)

    cropped_images = []
    # Draw the convex hulls of the contours on the mask
    for contour in contours:
        hull = cv2.convexHull(contour)
        x, y, w, h = cv2.boundingRect(hull)
        # Crop the original image using the bounding rectangle coordinates
        cropped_image = objects_gray[y:y+h, x:x+w]
        cropped_images.append(cropped_image)
        cv2.drawContours(hull_mask, [hull], -1, (255), thickness=cv2.FILLED)

    # Apply the convex hull mask to the grayscale objects image
    objects_gray[hull_mask == 0] = 0

    return objects_gray,dicecount,cropped_images



# predict 30 X30 image if in 1-6 
def predict_dice(frame):
    """
    Predicts the number of eyes on a dice in a given frame using a pre-trained TensorFlow Lite model.

    Args:
        frame: A numpy array representing the image frame.

    Returns:
        A numpy array representing the predicted number of eyes on the dice.
    """
    # Convert frame to grayscale if not already done
    if len(frame.shape) > 2 and frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Resize the image to match the input shape expected by the model
    frame = cv2.resize(frame, (input_shape_dice[1], input_shape_dice[2]))

    # Convert the image to float32
    frame = frame.astype(np.float32)
    
    # Normalize the image if required 
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



def get_sum_in_image(img):
    """
    Given an image of dice, this function returns the sum of the number of eyes
    on each dice in the image.

    Args:
        img (numpy.ndarray): The input image of dice.

    Returns:
        int: The sum of the number of eyes on each dice in the input image.
    """
    class_labels_dice = ["1", "2", "3", "4", "5", "6"]
    img,_, cropped_images = process_image(img)

    sum_in_image=0
    prediction_state = True
    
    for i in range(len(cropped_images)):
        # Exception if cropped image is not nearly quadratic -> inidcating some dices are not detected
        #print("(cropped_images[i].shape[0] / cropped_images[i].shape[1])",(cropped_images[i].shape[0] / cropped_images[i].shape[1]))
        # TODO implement a better check for this case : idea : size of the image should be in a certain range..
        if  (cropped_images[i].shape[0] / cropped_images[i].shape[1]) > 1.4 or (cropped_images[i].shape[1] / cropped_images[i].shape[0]) < (1. / 1.4):
            prediction_state = False
        else :
            pass 
        
        
        frame = cv2.resize(cropped_images[i], (30, 30))
        
        output_data_dice = predict_dice(frame)
        prediction_dice = np.argmax(output_data_dice)
        dice_label = class_labels_dice[prediction_dice]
        sum_in_image+=int(dice_label)
    return sum_in_image , prediction_state


