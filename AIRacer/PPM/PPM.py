import json
import socket
import serial
import time

class My_PPM:
    def __init__(self):
        print("starting PPM init")
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 2137
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
        self.ser = serial.Serial()
        self.ser.timeout = 1
        self.ser.baudrate = 115200
        self.ser.port = 'COM7'
        self.ser.open()
        self.lastChristmas = time.time()


    def update_ppm_channels(self, values):
        if  time.time() - self.lastChristmas > 0.1:
            self.lastChristmas = time.time()
            # start = time.time()
            # self.ppm.update_channels(values)
            # print("PPM took", time.time()-start, " sec")
            print("JP2GMD")
            print(values)
            data = json.dumps(values).replace("[", "").replace("]", "") + "\n"
            self.sock.sendto(bytes(data, "utf-8"), (self.UDP_IP, self.UDP_PORT))
            self.ser.write(bytes(data, "utf-8"))
            print(self.ser.readline())
            #print(bytes(data, "utf-8"))
        else:
            []
        []

    def stop(self):
        # self.ppm.cancel()
        # self.pi.stop()
        []