import cv2
import csv
import os

from PyQt5.QtCore import QTimer, QPoint, pyqtSlot
from PyQt5.QtGui import QPainter, QImage
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QGridLayout, QPushButton

from settings.settings import Values


class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()


class ImageWindow(QMainWindow):

    def __init__(self, main_loop):
        super().__init__()
        self.main_loop = main_loop
        self.central_widget = QWidget(self)
        self.setWindowTitle("AI Racer")
        P_label = QLabel("P")
        I_label = QLabel("I")
        D_label = QLabel("D")

        self.yaw = QLabel("Yaw")
        self.yaw_ppm_label = QLabel("ppm")
        self.yaw_P = QLineEdit("0")
        self.yaw_I = QLineEdit("1")
        self.yaw_D = QLineEdit("2")

        self.roll_ppm_label = QLabel("ppm")
        self.roll = QLabel("Roll")
        self.roll_P = QLineEdit("3")
        self.roll_I = QLineEdit("4")
        self.roll_D = QLineEdit("5")

        self.throttle_ppm_label = QLabel("ppm")
        self.throttle = QLabel("Throttle")
        self.throttle_P = QLineEdit("6")
        self.throttle_I = QLineEdit("7")
        self.throttle_D = QLineEdit("8")

        self.layout = QGridLayout()
        self.displays = QVBoxLayout()

        self.layout.addWidget(self.yaw_ppm_label, 0, 1)
        self.layout.addWidget(self.roll_ppm_label, 0, 2)
        self.layout.addWidget(self.throttle_ppm_label, 0, 3)

        self.layout.addWidget(P_label, 2, 0)
        self.layout.addWidget(I_label, 3, 0)
        self.layout.addWidget(D_label, 4, 0)
        self.disp = ImageWidget(self)

        self.layout.addWidget(self.yaw, 1, 1)
        self.layout.addWidget(self.yaw_P, 2, 1)
        self.layout.addWidget(self.yaw_I, 3, 1)
        self.layout.addWidget(self.yaw_D, 4, 1)

        self.layout.addWidget(self.roll, 1, 2)
        self.layout.addWidget(self.roll_P, 2, 2)
        self.layout.addWidget(self.roll_I, 3, 2)
        self.layout.addWidget(self.roll_D, 4, 2)

        self.layout.addWidget(self.throttle, 1, 3)
        self.layout.addWidget(self.throttle_P, 2, 3)
        self.layout.addWidget(self.throttle_I, 3, 3)
        self.layout.addWidget(self.throttle_D, 4, 3)

        self.update_button = QPushButton("Update PID")
        self.update_button.clicked.connect(self.on_click_update)
        self.layout.addWidget(self.update_button, 5, 1)

        self.start_button = QPushButton("Start PIDs and PPM")
        self.start_button.clicked.connect(self.on_click_start)
        self.layout.addWidget(self.start_button, 6, 2)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_click_stop)
        self.layout.addWidget(self.stop_button, 6, 3)

        self.stop_button = QPushButton("Start PIDs")
        self.stop_button.clicked.connect(self.on_click_update_pids)
        self.layout.addWidget(self.stop_button, 6, 1)

        self.displays.addWidget(self.disp)

        self.displays.addLayout(self.layout)

        self.central_widget.setLayout(self.displays)
        self.setCentralWidget(self.central_widget)
        self.show_pid_values()

    @pyqtSlot()
    def on_click_update(self):
        lines = [self.yaw_P.text() + ',' + self.roll_P.text() + ',' + self.throttle_P.text() + '\n',
                 self.yaw_I.text() + ',' + self.roll_I.text() + ',' + self.throttle_I.text() + '\n',
                 self.yaw_D.text() + ',' + self.roll_D.text() + ',' + self.throttle_D.text() + '\n']
        with open(os.path.join("settings", "pidValues.csv"), 'w') as fd:
            fd.writelines(lines)

        self.main_loop.pids.yawPID.Kp = float(self.yaw_P.text())
        self.main_loop.pids.yawPID.Ki = float(self.yaw_I.text())
        self.main_loop.pids.yawPID.Kd = float(self.yaw_D.text())
        self.main_loop.pids.rollPID.Kd = float(self.roll_P.text())
        self.main_loop.pids.rollPID.Ki = float(self.roll_I.text())
        self.main_loop.pids.rollPID.Kd = float(self.roll_D.text())
        self.main_loop.pids.throttlePID.Kp = float(self.roll_P.text())
        self.main_loop.pids.throttlePID.Ki = float(self.roll_I.text())
        self.main_loop.pids.throttlePID.Kd = float(self.roll_D.text())

    @pyqtSlot()
    def on_click_start(self):
        self.pid_start()

    @pyqtSlot()
    def on_click_stop(self):
        self.pid_stop()

    @pyqtSlot()
    def on_click_update_pids(self):
        self.main_loop.pids.update_pids = True

    def pid_start(self):
        self.main_loop.pids.update_ppm = True
        self.main_loop.pids.update_pids = True

    def pid_stop(self):
        self.main_loop.pids.update_ppm = False
        self.main_loop.pids.update_pids = False

    def start(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.show_image(self.main_loop.detector.frame, self.disp))
        self.timer.start(Values.GUI_UPDATE_MS)

    def show_image(self, image, display):
        self.throttle_ppm_label.setText(str(round(self.main_loop.pids.throttlePID.output_ppm, 1)))
        self.yaw_ppm_label.setText(str(round(self.main_loop.pids.yawPID.output_ppm, 1)))
        self.roll_ppm_label.setText(str(round(self.main_loop.pids.rollPID.output_ppm, 1)))
        if image is not None:
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            disp_size = img.shape[1], img.shape[0]
            disp_bpl = disp_size[0] * 3
            img = cv2.resize(img, disp_size, interpolation=cv2.INTER_CUBIC)
            qimg = QImage(img.data, disp_size[0], disp_size[1], disp_bpl, QImage.Format_RGB888)
            display.setImage(qimg)

    def flush(self):
        pass

    def closeEvent(self, event):
        print("Image window closed!")
        self.main_loop.close()

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.pid_start()
        if event.key() == 16777216:
            self.pid_stop()

    def show_pid_values(self):
        self.yaw_P.setText(str(self.main_loop.pids.yawPID.Kp))
        self.yaw_I.setText(str(self.main_loop.pids.yawPID.Ki))
        self.yaw_D.setText(str(self.main_loop.pids.yawPID.Kd))
        self.roll_P.setText(str(self.main_loop.pids.rollPID.Kp))
        self.roll_I.setText(str(self.main_loop.pids.rollPID.Ki))
        self.roll_D.setText(str(self.main_loop.pids.rollPID.Kd))
        self.throttle_P.setText(str(self.main_loop.pids.throttlePID.Kp))
        self.throttle_I.setText(str(self.main_loop.pids.throttlePID.Ki))
        self.throttle_D.setText(str(self.main_loop.pids.throttlePID.Kd))


class RemoteImageWindow(QMainWindow):

    def __init__(self, main_loop):
        super().__init__()
        self.main_loop = main_loop
        self.central_widget = QWidget(self)
        self.setWindowTitle("AI Racer")
        P_label = QLabel("P")
        I_label = QLabel("I")
        D_label = QLabel("D")

        values = self.get_pid_values()
        self.yaw = QLabel("Yaw")
        self.yaw_ppm_label = QLabel("1500")
        self.yaw_P = QLineEdit(values[0][0])
        self.yaw_I = QLineEdit(values[1][0])
        self.yaw_D = QLineEdit(values[2][0])

        self.roll_ppm_label = QLabel("1500")
        self.roll = QLabel("Roll")
        self.roll_P = QLineEdit(values[0][1])
        self.roll_I = QLineEdit(values[1][1])
        self.roll_D = QLineEdit(values[2][1])

        self.throttle_ppm_label = QLabel("1000")
        self.throttle = QLabel("Throttle")
        self.throttle_P = QLineEdit(values[0][2])
        self.throttle_I = QLineEdit(values[1][2])
        self.throttle_D = QLineEdit(values[2][2])

        self.layout = QGridLayout()
        self.displays = QVBoxLayout()

        self.layout.addWidget(self.yaw_ppm_label, 0, 1)
        self.layout.addWidget(self.roll_ppm_label, 0, 2)
        self.layout.addWidget(self.throttle_ppm_label, 0, 3)

        self.layout.addWidget(P_label, 2, 0)
        self.layout.addWidget(I_label, 3, 0)
        self.layout.addWidget(D_label, 4, 0)
        self.disp = ImageWidget(self)

        self.layout.addWidget(self.yaw, 1, 1)
        self.layout.addWidget(self.yaw_P, 2, 1)
        self.layout.addWidget(self.yaw_I, 3, 1)
        self.layout.addWidget(self.yaw_D, 4, 1)

        self.layout.addWidget(self.roll, 1, 2)
        self.layout.addWidget(self.roll_P, 2, 2)
        self.layout.addWidget(self.roll_I, 3, 2)
        self.layout.addWidget(self.roll_D, 4, 2)

        self.layout.addWidget(self.throttle, 1, 3)
        self.layout.addWidget(self.throttle_P, 2, 3)
        self.layout.addWidget(self.throttle_I, 3, 3)
        self.layout.addWidget(self.throttle_D, 4, 3)

        self.update_button = QPushButton("Update PID")
        self.update_button.clicked.connect(self.on_click_update)
        self.layout.addWidget(self.update_button, 5, 1)

        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_click_start)
        self.layout.addWidget(self.start_button, 5, 2)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.on_click_stop)
        self.layout.addWidget(self.stop_button, 5, 3)

        self.displays.addWidget(self.disp)

        self.displays.addLayout(self.layout)

        self.central_widget.setLayout(self.displays)
        self.setCentralWidget(self.central_widget)

    @pyqtSlot()
    def on_click_update(self):
        lines = [self.yaw_P.text() + ',' + self.roll_P.text() + ',' + self.throttle_P.text() + '\n',
                 self.yaw_I.text() + ',' + self.roll_I.text() + ',' + self.throttle_I.text() + '\n',
                 self.yaw_D.text() + ',' + self.roll_D.text() + ',' + self.throttle_D.text() + '\n']
        with open(os.path.join("settings", "pidValues.csv"), 'w') as fd:
            fd.writelines(lines)

        output_str = "p"
        for line in lines:
            output_str += line
        self.main_loop.tcp_server.socket.send(output_str.encode())

    @pyqtSlot()
    def on_click_start(self):
        self.pid_start()

    @pyqtSlot()
    def on_click_stop(self):
        self.pid_stop()

    def pid_start(self):
        try:
            self.main_loop.tcp_server.socket.send("s".encode())
        except:
            print("Cant send message")

    def pid_stop(self):
        try:
            self.main_loop.tcp_server.socket.send("x".encode())
        except:
            print("Cant send message")

    def start(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.show_image_update_ppm(self.main_loop.frame, self.disp))
        self.timer.start(Values.GUI_UPDATE_MS)

    def show_image_update_ppm(self, image, display):
        self.update_ppm_values()
        if image is not None:
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            disp_size = img.shape[1], img.shape[0]
            disp_bpl = disp_size[0] * 3
            img = cv2.resize(img, disp_size, interpolation=cv2.INTER_CUBIC)
            qimg = QImage(img.data, disp_size[0], disp_size[1], disp_bpl, QImage.Format_RGB888)
            display.setImage(qimg)

    def flush(self):
        pass

    def closeEvent(self, event):
        self.main_loop.close()

    def update_ppm_values(self):
        self.throttle_ppm_label.setText(str(self.main_loop.tcp_throttle))
        self.yaw_ppm_label.setText(str(self.main_loop.tcp_yaw))
        self.roll_ppm_label.setText(str(self.main_loop.tcp_roll))

    def keyPressEvent(self, event):
        if event.key() == 16777220:
            self.pid_start()
        if event.key() == 16777216:
            self.pid_stop()

    def get_pid_values(self):
        values = []
        with open(os.path.join("settings", "pidValues.csv"), 'r') as fd:
            reader = csv.reader(fd)
            for row in reader:
                values.append(row)
        return values
