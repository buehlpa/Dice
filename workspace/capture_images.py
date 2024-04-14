import cv2

def main():
    # Open the default camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_EXPOSURE, 50)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Create a window to display the camera feed
    cv2.namedWindow("Camera Feed")

    # Counter to keep track of captured images
    img_counter = 0

    while True:
        # Capture frame-by-frame
        ret, frame = cap.read()
        frame= frame[:470,:,:]

        if not ret:
            print("Error: Failed to capture frame.")
            break

        # Display the resulting frame
        cv2.imshow("Camera Feed", frame)

        # Check for spacebar press
        key = cv2.waitKey(1)
        if key == 32:  # Spacebar key
            img_name = "captured_image_{}.png".format(img_counter)
            cv2.imwrite(img_name, frame)
            print("{} saved".format(img_name))
            img_counter += 1
        elif key == 27:  # ESC key
            print("Escape key pressed. Exiting...")
            break

    # Release the camera and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
