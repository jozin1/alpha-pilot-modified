import socket
from settings.settings import Values
from PIDs.PIDs import PIDs
import time
import os
from threading import Thread


class TCPclient(Thread):

    def __init__(self, pids: PIDs):
        Thread.__init__(self)
        try:
            self.pids = pids
            self.ip = Values.REMOTE_IP
            self.port = Values.TCP_PORT
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.connect((self.ip, self.port))
            self.last_yaw_output = self.pids.yawPID.output_ppm
            self.last_roll_output = self.pids.rollPID.output_ppm
            self.last_throttle_output = self.pids.throttlePID.output_ppm
        except:
            self.pids.stop()

    def run(self):
        t1 = Thread(target=self.handle_receive)
        t2 = Thread(target=self.handle_send)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    def handle_receive(self):
        while True:
            try:
                data = self.socket.recv(1024).decode()
                if data == "s":
                    self.pids.update_ppm = True
                    self.pids.update_pids = True
                elif data == "x":
                    self.pids.update_ppm = False
                    self.pids.update_pids = False
                elif data[0] == "p":
                    with open(os.path.join("settings", "pidValues.csv"), 'w') as fd:
                        fd.write(data[1:])
                    lines = data[1:].split("\n")
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
            except:
                self.pids.stop()
                break

    def handle_send(self):
        while True:
            try:
                if self.pids.yawPID.output_ppm != self.last_yaw_output:
                    self.socket.send(("y" + str(round(self.pids.yawPID.output_ppm, 1))).encode())
                    self.last_yaw_output = self.pids.yawPID.output_ppm
                    time.sleep(0.03)

                if self.pids.rollPID.output_ppm != self.last_roll_output:
                    self.socket.send(("r" + str(round(self.pids.rollPID.output_ppm, 1))).encode())
                    self.last_roll_output = self.pids.rollPID.output_ppm
                    time.sleep(0.03)

                if self.pids.throttlePID.output_ppm != self.last_throttle_output:
                    self.socket.send(("t" + str(round(self.pids.throttlePID.output_ppm, 1))).encode())
                    self.last_throttle_output = self.pids.throttlePID.output_ppm
                    time.sleep(0.03)
                time.sleep(0.05)
            except:
                self.pids.stop()
                print("socket sending error")

    def close(self):
        self.socket.close()


