import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QLineEdit
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

class VideoStreamWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.video_capture = cv2.VideoCapture(0)
        self.init_ui()
        self.update_frame()
        self.name = ""
        self.score = 0

    def init_ui(self):
        
        
        self.image_label = QLabel(self)
        self.histogram_label = QLabel(self)
        
        
        self.reset_button = QPushButton('Reset Histogram', self)
        self.reset_button.clicked.connect(self.reset_histogram)

        self.name_entry = QLineEdit(self)
        self.name_entry.setPlaceholderText("Enter name here")
        self.name_entry.returnPressed.connect(self.update_name_score)

        self.score_label = QLabel("Name: \nScore: ", self)
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        layout.addWidget(self.histogram_label)
        layout.addWidget(self.reset_button, alignment=Qt.AlignCenter)
        layout.addWidget(self.name_entry)
        layout.addWidget(self.score_label)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # refresh every 30 ms

        self.reset_histogram()  # Initialize the histogram

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, aspectRatioMode=Qt.KeepAspectRatio)
            self.image_label.setPixmap(QPixmap.fromImage(p))

    def reset_histogram(self):
        
        # just some random code to show that wen can use matplotlib 
        # Generate a new histogram plot
        fig = Figure()
        canvas = FigureCanvas(fig)
        ax = fig.add_subplot(111)
        random_numbers = np.random.randn(1000)
        ax.hist(random_numbers, bins=30)
        ax.set_xlabel('Value')
        ax.set_ylabel('Frequency')
        ax.set_title('Histogram of Random Numbers')

        # Render the plot to a canvas and then convert to a QPixmap
        canvas.draw()
        width, height = fig.get_size_inches() * fig.get_dpi()
        image = np.fromstring(canvas.tostring_rgb(), dtype='uint8').reshape(int(height), int(width), 3)
        qt_image = QImage(image.data, image.shape[1], image.shape[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.histogram_label.setPixmap(pixmap.scaled(self.histogram_label.size(), Qt.KeepAspectRatio))

    def update_name_score(self):
        self.name = self.name_entry.text()
        self.score = np.random.randint(0, 101)  # Random score between 0 and 100
        self.score_label.setText(f"Name: {self.name}\nScore: {self.score}")

    def closeEvent(self, event):
        self.video_capture.release()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = VideoStreamWidget()
    main_window.show()
    sys.exit(app.exec_())
