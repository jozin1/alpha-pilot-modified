from threading import Thread
from detector.detector3 import Detector
from settings.settings import Values
from camera.camera import Camera2
from PIDs.PIDs import PIDs
import cv2
import time


class MainLoop(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.detector = Detector(Values.MODEL_PATH)
        self.camera = Camera2()
        self.pids = PIDs()
        self.stop_loop = False
        self.frame = cv2.imread("images/start.jpg")

        if Values.REMOTE_CONTROL:
            from TCPclient.TCPclient import TCPclient
            self.tcpClient = TCPclient(self.pids)
            self.tcpClient.start()

        if Values.SEND_IMAGES_WIFI:
            from imageStream.imageStream import ImageStream
            self.imageStream = ImageStream()

    def run(self):
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

                if Values.SEND_IMAGES_WIFI:
                    self.imageStream.send_image(cv2.resize(self.detector.frame, Values.SENT_IMAGES_SIZE))

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

    def close(self):
        self.stop_loop = True
