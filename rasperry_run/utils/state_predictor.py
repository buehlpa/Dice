
import numpy as np
import cv2
import tflite_runtime.interpreter as tflite
import os


model_dir = 'models'
model_file = 'model_dices_eyes2.tflite'
MODEL_PATH = os.path.join(model_dir, model_file)

class_labels_state = ["empty", "rolling", "still"]


###  Load the TFLite model and allocate tensors.
# state interpreter model detects the state of the scene
interpreter_state = tflite.Interpreter(model_path=MODEL_PATH)
interpreter_state.allocate_tensors()

# Get model details
input_details_state = interpreter_state.get_input_details()
output_details_state = interpreter_state.get_output_details()
input_shape_state = input_details_state[0]['shape']



def predict_state(frame_resized):
    """
    Predicts the state of a dice from a given image frame.

    Args:
        frame_resized (numpy.ndarray): The resized image frame of the dice.

    Returns:
        str: The predicted state of the dice (["empty", "rolling", "still"]).
    """
    
    input_data = np.expand_dims(frame_resized, axis=0)
    if input_details_state[0]['dtype'] == np.float32:
        input_data = (np.float32(input_data) - 127.5) / 127.5

    # Feed the frame to the state model
    interpreter_state.set_tensor(input_details_state[0]['index'], input_data)
    interpreter_state.invoke()

    # Retrieve the results and determine the class with the highest probability
    output_data_state = interpreter_state.get_tensor(output_details_state[0]['index'])
    prediction_state = np.argmax(output_data_state)
    class_label_state = class_labels_state[prediction_state]
    return class_label_state
    