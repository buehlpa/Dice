import sys
import cv2
import queue
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QThread
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtGui import QPainter, QColor, QFont



class VideoCaptureThread(QThread):
    # Signal to output the captured frame
    frame_captured = pyqtSignal(QImage)
    def __init__(self, queue):
        super().__init__()
        self.running = True

    def run(self):
        cap = cv2.VideoCapture(0)        
        while self.running:
            ret, frame = cap.read()
            if ret:
                # Convert the frame to Qt format
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)       
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.frame_captured.emit(qt_image)

    def stop(self):
        self.running = False
        self.wait()



class StatePredictorThread(QThread):
    state_prediction_signal = pyqtSignal(str)
    
    def __init__(self, name):
        super().__init__()
        self.name = name

    @pyqtSlot(QImage)
    def process_image(self, image):
        
        #TODO implement state prediciton
        # convert q image back to opencv
        # put in que
        # get from que
        # process with algo
        # put in output que 
        # state_prediction =get from output que
        
        # time.sleep(1.5)
        state=np.random.randint(1,7)
        state_prediction = f"State: {state}"
        self.state_prediction_signal.emit(state_prediction)


class DicePredictorThread(QThread):
    dice_prediction_signal = pyqtSignal(int)
    def __init__(self, name):
        super().__init__()
        self.name = name

    @pyqtSlot(QImage)
    def process_image(self, image): ## TODO implement dice prediciton
        
        #TODO implement dice prediciton
        # convert q image back to opencv
        # put in que
        # get from que
        # process with algo
        # put in output que 
        # state_prediction =get from output que
        
        # BUG time sleep blocks the main thread , as well as cpu intensive tasks try other method, this is not tested yet
        dice_prediction = np.random.randint(1,7)
        self.dice_prediction_signal.emit(dice_prediction)



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.label = QLabel(self)
        self.initUI()
        self.state_prediciton = "State: "
        
        self.dice_predicition = "Dice: "
        
        # Queue for frames
        self.frame_queue = queue.Queue()
        #TODO implement state prediciton and dice prediciton queues


        # Initialize and start the video capture thread
        self.capture_thread = VideoCaptureThread(self.frame_queue)
        self.capture_thread.frame_captured.connect(self.update_image)
        self.capture_thread.start()
        # State Predficition Thread
        self.state_thread = StatePredictorThread("State Thread")
        self.capture_thread.frame_captured.connect(self.state_thread.process_image)
        # Dice Prediciton Thread
        self.dice_thread = DicePredictorThread("Dice Thread")
        self.capture_thread.frame_captured.connect(self.dice_thread.process_image)
        
        # connect the siganls from the threads
        self.dice_thread.dice_prediction_signal.connect(self.handle_dice_prediction)
        self.state_thread.state_prediction_signal.connect(self.handle_state_prediction)
        


    def initUI(self):
        self.setWindowTitle('PyQt5 Video')
        self.setGeometry(100, 100, 800, 600)
        self.label = QLabel(self)
        self.label.resize(640, 480)
        self.show()
        # TODO design gui  camera feed etc ,  text boxes and histogram plot



    @pyqtSlot(QImage)
    def update_image(self, qt_image):
        # Create a QPainter instance and begin the painting process on the image
        painter = QPainter(qt_image)
        painter.begin(self)
        painter.setPen(QColor(255, 255, 255))  # White color
        painter.setFont(QFont('Arial', 20))  # Change font and size as needed
        painter.drawText(10, 30, self.state_prediciton)
        painter.drawText(10, 80, f"Dice: {self.dice_predicition}")
        # End the painting process
        painter.end()
        # Convert the QImage (with the text) to QPixmap and set it to the label
        self.label.setPixmap(QPixmap.fromImage(qt_image))

    ## TODO logic for saving automatically to file 
    @pyqtSlot(str)
    def handle_state_prediction(self, prediction):
        self.state_prediciton = prediction
        print(f"state prediction: {prediction}")

    @pyqtSlot(int)
    def handle_dice_prediction(self, prediction):
        self.dice_predicition = prediction
        print(f"Dice prediction: {str(prediction)}")


    def closeEvent(self, event):
        self.capture_thread.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    sys.exit(app.exec_())
