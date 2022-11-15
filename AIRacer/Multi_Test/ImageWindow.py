import csv
import os
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QLabel
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QGridLayout, QPushButton


class ImageWindow(QMainWindow):

    def __init__(self, conn):
        self.conn = conn
        super().__init__()
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

        output_str = "p"
        for line in lines:
            output_str += line
        self.conn.send(output_str)

    @pyqtSlot()
    def on_click_start(self):
        self.pid_start()

    @pyqtSlot()
    def on_click_stop(self):
        self.pid_stop()

    def pid_start(self):
        self.conn.send("s")

    def pid_stop(self):
        self.conn.send("x")

    def flush(self):
        pass

    def closeEvent(self, event):
        print("Image window closed!")
        self.conn.send("e")

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

    def show_pid_values(self):
        values = self.get_pid_values()

        self.yaw_P.setText(str(values[0][0]))
        self.yaw_I.setText(str(values[1][0]))
        self.yaw_D.setText(str(values[2][0]))
        self.roll_P.setText(str(values[0][1]))
        self.roll_I.setText(str(values[1][1]))
        self.roll_D.setText(str(values[2][1]))
        self.throttle_P.setText(str(values[0][2]))
        self.throttle_I.setText(str(values[1][2]))
        self.throttle_D.setText(str(values[2][2]))