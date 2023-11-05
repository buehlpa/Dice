import cv2
import csv
import utils.threading_utils as tu
import pandas as pd
import matplotlib.pyplot as plt

# Function to plot histogram
def plot_histogram(csv_file_path):
    # Read the data from CSV file without a header
    data = pd.read_csv(csv_file_path, header=None)
    
    # If the file is empty, do not plot
    if data.empty:
        print("The CSV file is empty. No data to plot.")
        return
    
    # Assuming the data you want is in the first column
    dice_data = data[0]
    
    # Plot the histogram
    plt.figure("Histogram")
    plt.hist(dice_data, bins=range(1, int(dice_data.max()) + 2), edgecolor='black')
    plt.title('Dice Roll Distribution')
    plt.xlabel('Dice Sum')
    plt.ylabel('Frequency')
    
    # Show the plot in a non-blocking way
    plt.show(block=False)


# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Cannot open camera")
    exit()

# Start the worker threads for stateprediciton and dice prediction
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


    # save result to file  by pressing space and 
    if cv2.waitKey(1) & 0xFF == ord(' '):
            with open('results/res.csv', mode='a') as file:
                writer = csv.writer(file)
                writer.writerow([dice_sum])
            plot_histogram('results/res.csv')
            
    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        plt.close('all')
        break


tu.stop_workers()  # Stop worker threads
cap.release()
cv2.destroyAllWindows()
