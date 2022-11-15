import time
from threading import Thread
from camera.camera import Camera2
from detector.detector import Detector
from settings.settings import Values
from PIDs.PIDs import multiPIDs
import cv2


class Process2:
    def __init__(self, child_conn):
        self.child_conn = child_conn
        self.detector = None
        self.camera = None
        self.pids = None
        self.stop_loop = False
        self.frame = cv2.imread("images/start.jpg")

        if Values.REMOTE_CONTROL:
            self.tcpClient = None

        if Values.SEND_IMAGES_WIFI:
            self.imageStream = None

    def receive(self):
        while True:
            msg = self.child_conn.recv()
            print("child received: ", msg)
            if msg == "s":
                self.pids.update_pids = True
                self.pids.update_ppm = True
            elif msg == "x":
                self.pids.update_pids = False
                self.pids.update_ppm = False
            elif msg == "e":
                self.child_conn.send("e")
                self.stop_loop = True
                break
            elif msg[0] == "p":
                lines = msg[1:].split("\n")
                values = []
                for l in lines:
                    values.append(l.split(","))
                self.pids.yawPID.Kp = float(values[0][0])
                self.pids.yawPID.Ki = float(values[1][0])
                self.pids.yawPID.Kd = float(values[2][0])

                self.pids.rollPID.Kp = float(values[0][1])
                self.pids.rollPID.Ki = float(values[1][1])
                self.pids.rollPID.Kd = float(values[2][1])

                self.pids.throttlePID.Kp = float(values[0][2])
                self.pids.throttlePID.Ki = float(values[1][2])
                self.pids.throttlePID.Kd = float(values[2][2])

        self.child_conn.close()

    def start(self):
        t1 = Thread(target=self.receive)
        t1.start()

        self.detector = Detector(Values.MODEL_PATH)
        self.camera = Camera2()
        self.pids = multiPIDs(self.child_conn)
        self.stop_loop = False
        self.frame = cv2.imread("images/start.jpg")

        try:
            if Values.PRINT_FPS:
                last_time = time.time()
                ind = 0
            while True:
                if self.stop_loop:
                    break

                self.frame = self.camera.get_frame()

                if self.frame is None:
                    continue

                mid, ratio = self.detector.detect(self.frame)  # mid liczony od: lewy gorny rog
                self.pids.update(mid, ratio)

                cv2.imshow("Drone view", self.detector.frame)
                cv2.waitKey(1)

                if Values.PRINT_FPS:
                    ind += 1
                    if time.time() - last_time > 1:
                        print("FPS:", ind)
                        ind = 0
                        last_time = time.time()

        except ValueError as er:
            print("Some error accured: ", str(er))
        except KeyboardInterrupt:
            print("Closing")
        finally:
            self.camera.close()
            self.pids.stop()
