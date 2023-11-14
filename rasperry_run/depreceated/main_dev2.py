import sys
import cv2
from PyQt5.QtCore import QThread, Qt, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QApplication
import queue
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
import time

# Define the functions a() and b()
def a(rgbImage):
    # ... processing logic for function a ...
    # Convert the image to grayscale as a dummy processing step
    rgbImage = cv2.cvtColor(rgbImage, cv2.COLOR_RGB2GRAY)
    return rgbImage

def b(rgbImage):
    # ... processing logic for function b ...
    # Dummy processing step
    time.sleep(0.5)
    return "a"


# Thread class for function a
class ThreadA(QThread):
    def __init__(self, input_queue, output_queue):
        QThread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        while True:
            rgbImage = self.input_queue.get()
            if rgbImage is None:  # None is a signal to stop
                return
            result = a(rgbImage)  # Process the image
            self.output_queue.put(result)

# Thread class for function b
class ThreadB(QThread):
    def __init__(self, input_queue, output_queue):
        QThread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        while True:
            rgbImage = self.input_queue.get()
            if rgbImage is None:  # None is a signal to stop
                return
            result = b(rgbImage)  # Process the image
            self.output_queue.put(result)

# PyQt thread class for video capture
class CaptureThread(QThread):
    changePixmap = pyqtSignal(QImage)

    def __init__(self, input_queue_a, input_queue_b):
        QThread.__init__(self)
        self.input_queue_a = input_queue_a
        self.input_queue_b = input_queue_b
        self.thread_b_output_queue = 

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Unable to access the camera")
        else:
            print("Starting video capture...")

        while True:
            ret, frame = cap.read()
            if ret:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                if not self.input_queue_a.full():
                    self.input_queue_a.put(rgbImage.copy())  # Put a copy of the image in the input queue A
                if not self.input_queue_b.full():
                    self.input_queue_b.put(rgbImage.copy())  # Put a copy of the image in the input queue B

                #print(self.input_queue_b.get())
                print(self.thread_b_output_queue.get())
                
                
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
            else:
                print("Failed to capture video frame")
                break

        cap.release()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.input_queue_a = queue.Queue(maxsize=5)
        self.input_queue_b = queue.Queue(maxsize=5)
        self.thread_a_output_queue = queue.Queue()
        self.thread_b_output_queue = queue.Queue()
        
        self.threadA = ThreadA(self.input_queue_a, self.thread_a_output_queue)
        self.threadB = ThreadB(self.input_queue_b, self.thread_b_output_queue)
        self.captureThread = CaptureThread(self.input_queue_a, self.input_queue_b)

        self.threadA.start()
        self.threadB.start()
        self.captureThread.changePixmap.connect(self.setImage)
        self.captureThread.start()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('PyQt5 Video')
        self.setGeometry(100, 100, 800, 600)
        self.label = QLabel(self)
        self.label.resize(640, 480)
        self.captureThread.changePixmap.connect(self.setImage)
        self.show()

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def closeEvent(self, event):
        self.input_queue_a.put(None)  # Signal to threads A to stop
        self.input_queue_b.put(None)  # Signal to threads B to stop
        self.captureThread.terminate()
        self.captureThread.wait()
        self.threadA.terminate()
        self.threadA.wait()
        self.threadB.terminate()
        self.threadB.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
