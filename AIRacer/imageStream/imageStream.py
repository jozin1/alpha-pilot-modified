import base64
import zmq
from settings.settings import Values
import cv2


class ImageStream:
    def __init__(self):
        context = zmq.Context()
        self.footage_socket = context.socket(zmq.PUB)
        self.footage_socket.connect('tcp://' + Values.REMOTE_IP + ':' + str(Values.IMAGE_STREAM_PORT))

    def send_image(self, frame):
        encoded, buffer = cv2.imencode('.jpg', frame)
        jpg_as_text = base64.b64encode(buffer)
        self.footage_socket.send(jpg_as_text)