import multiprocessing
import random



def get_sum_in_image(frame):
    new = random.choice([1, 2, 3, 4, 5, 6])
    print(new)
    return new, True

dice_input_queue = multiprocessing.Queue(maxsize=5)
dice_output_queue = multiprocessing.Queue(maxsize=5)


def dice_worker():
    while True:
        frame = dice_input_queue.get()
        if frame is None:  # Exit signal
            break
        try:
            dice_predicted_sum, dice_prediction_pass = get_sum_in_image(frame)
            dice_output_queue.put((dice_predicted_sum, dice_prediction_pass))
        except Exception as e:
            dice_output_queue.put(e)

def start_workers():
    # Start worker process
    multiprocessing.Process(target=dice_worker )

def stop_workers():
    # Signal the worker process to stop
    dice_input_queue.put(None)

def enqueue_frame(frame):
    dice_input_queue.put(frame)

def enqueue_frame_for_dice(frame):
    dice_input_queue.put(frame)

def get_dice_prediction():
    if not dice_output_queue.empty():
        return dice_output_queue.get()