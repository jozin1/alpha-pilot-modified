from threading import Thread
from settings.settings import Values
from TCPserver.TCPserver import TCPserver
import cv2
import time
import base64
import numpy as np
import zmq


class ServerMainLoop(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.tcp_server = TCPserver(Values.TCP_PORT)
        self.tcp_throttle = 1000
        self.tcp_roll = 1500
        self.tcp_yaw = 1500
        self.stop_loop = False
        self.frame = None

    def run(self):
        t1 = Thread(target=self.handle_receive)
        t1.start()
        if Values.SEND_IMAGES_WIFI:
            context = zmq.Context()
            footage_socket = context.socket(zmq.SUB)
            footage_socket.bind('tcp://*:5555')
            footage_socket.setsockopt_string(zmq.SUBSCRIBE, np.unicode(''))

        start = time.time()
        ind = 0

        while True:
            try:
                ind += 1
                if Values.SEND_IMAGES_WIFI:
                    received_string = footage_socket.recv_string()
                    img = base64.b64decode(received_string)
                    npimg = np.frombuffer(img, dtype=np.uint8)
                    self.frame = cv2.imdecode(npimg, 1)

                if time.time() - start > 1:
                    start = time.time()
                    print("FPS " + str(ind))
                    ind = 0

            except KeyboardInterrupt:
                cv2.destroyAllWindows()
                break

    def close(self):
        self.stop_loop = True

    def handle_receive(self):
        try:
            print("Started TCP server!")
            while 1:
                if self.stop_loop:
                    break
                newSocket, address = self.tcp_server.sock.accept()
                print("New client connected!")
                self.tcp_server.socket = newSocket
                while 1:
                    if self.stop_loop:
                        break
                    try:
                        receivedData = newSocket.recv(1024).decode()  # receive data from server
                        if receivedData[0] == "t":
                            self.tcp_throttle = receivedData[1:]
                        elif receivedData[0] == "y":
                            self.tcp_yaw = receivedData[1:]
                        elif receivedData[0] == "r":
                            self.tcp_roll = receivedData[1:]
                    except ConnectionResetError:
                        print("Lost connection!")
                newSocket.close()
        except KeyboardInterrupt:
            self.tcp_server.sock.close()
            self.tcp_server.socket.close()