import sys
import cv2
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class VideoStreamWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.video_capture = cv2.VideoCapture(0)
        self.init_ui()
        self.update_frame()

    def init_ui(self):
        self.image_label = QLabel(self)
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # refresh every 30 ms

    def update_frame(self):
        ret, frame = self.video_capture.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            p = convert_to_Qt_format.scaled(640, 480, aspectRatioMode=1)
            self.image_label.setPixmap(QPixmap.fromImage(p))

    def closeEvent(self, event):
        self.video_capture.release()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = VideoStreamWidget()
    main_window.show()
    sys.exit(app.exec_())
