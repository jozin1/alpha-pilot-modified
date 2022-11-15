import json
import socket

class My_PPM:
    def __init__(self):
        print("starting PPM init")
        self.UDP_IP = "127.0.0.1"
        self.UDP_PORT = 2137
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP


    def update_ppm_channels(self, values):
        # start = time.time()
        # self.ppm.update_channels(values)
        # print("PPM took", time.time()-start, " sec")
        data = json.dumps(values)
        self.sock.sendto(bytes(data, "utf-8"), (self.UDP_IP, self.UDP_PORT))
        []

    def stop(self):
        # self.ppm.cancel()
        # self.pi.stop()
        []