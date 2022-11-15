from threading import Thread
import cv2
from settings.settings import Values


class Camera2:
    def __init__(self):
        self.camera = cv2.VideoCapture(Values.CAMERA)

    def get_frame(self):
        ret, frame = self.camera.read()
        if ret:
            return frame
        else:
            return None

    def close(self):
        self.camera.release()
        cv2.destroyAllWindows()


class Camera(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.camera = cv2.VideoCapture(Values.CAMERA)
        self.frame = None
        self.stop = False
        self.new_frame = False

    def run(self):
        while True:
            if self.stop:
                break
            ret, self.frame = self.camera.read()
            self.new_frame = True
        self.camera.release()

    def get_frame(self):
        if self.new_frame:
            self.new_frame = False
            return self.frame
        else:
            return None

    def close(self):
        self.stop = True