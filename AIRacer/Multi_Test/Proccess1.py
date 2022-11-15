from threading import Thread
from Multi_Test.ImageWindow import ImageWindow
import sys
from PyQt5.QtWidgets import QApplication


class Process1:
    def __init__(self, parent_conn):
        self.parent_conn = parent_conn
        self.imageWindow = None

    def receive(self):
        while True:
            msg = self.parent_conn.recv()
            if msg[0] == "v":
                ppm = msg[1:].split(",")
                self.imageWindow.throttle_ppm_label.setText(ppm[2])
                self.imageWindow.roll_ppm_label.setText(ppm[1])
                self.imageWindow.yaw_ppm_label.setText(ppm[0])
            elif msg == "e":
                break
        self.parent_conn.close()

    def start(self):

        t1 = Thread(target=self.receive)
        t1.start()

        app = QApplication(sys.argv)
        self.imageWindow = ImageWindow(self.parent_conn)
        self.imageWindow.show()
        sys.exit(app.exec_())
