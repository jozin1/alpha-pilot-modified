from PID.PID import PID
from settings.settings import PIDSettings as ps
from settings.settings import Values
if not Values.WINDOWS_TESTS:
    from PPM.PPM import My_PPM
from threading import Timer
import csv
import os
import time


class PIDs:
    def __init__(self):
        self._timer = None
        self.dt = ps.PID_PPM_UPDATE_TIME
        self.is_running = False
        if not Values.WINDOWS_TESTS:            # do wywalenia pozniej bo szkoda obliczen
            self.ppm = My_PPM()
        self.update_ppm = False
        self.update_pids = False
        self.first_start = True
        values = self.get_pid_values()
        self.yawPID = PID(ps.YAW_SETPOINT, 1000, 2000, float(values[0][0]), float(values[1][0]), float(values[2][0]))
        self.rollPID = PID(ps.ROLL_SETPOINT, 1000, 2000, float(values[0][1]), float(values[1][1]), float(values[2][1]))
        self.throttlePID = PID(ps.THROTTLE_SETPOINT, 1000, 2000, float(values[0][2]), float(values[1][2]), float(values[2][2]))
        #pitchPID = PID(0.5, 1000, 2000, 1, 2, 3)

        self.last_yaw_ppm = 0
        self.last_roll_ppm = 0
        self.last_throttle_ppm = 0

        if Values.WRITE_TO_FILE:
            self.file = open('inputs_outputs.csv', 'a')
        if not Values.WINDOWS_TESTS:
            self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
        self.start()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.dt, self._run)
            self._timer.start()
            self.is_running = True

    def _run(self):
        self.is_running = False
        self.start()
        self.calculate_pids()
        self.send_ppm()

        if Values.WRITE_TO_FILE:
            self.write_to_file()

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        self.update_ppm = False         ################## ??????????? moze cos byc  nie tak
        self.update_pids = False
        if not Values.WINDOWS_TESTS:
            self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
        if Values.WRITE_TO_FILE:
            self.file.close()
        time.sleep(0.2)
        self.first_start = True

    def send_ppm(self):
        if not Values.WINDOWS_TESTS:
            if self.update_ppm:
                #
                if (int(self.throttlePID.output_ppm) != self.last_throttle_ppm) or \
                        (int(self.rollPID.output_ppm) != self.last_roll_ppm) or \
                        (int(self.yawPID.output_ppm) != self.last_yaw_ppm):

                    self.last_yaw_ppm = int(self.yawPID.output_ppm)
                    self.last_roll_ppm = int(self.rollPID.output_ppm)
                    self.last_throttle_ppm = int(self.throttlePID.output_ppm)

                    if self.first_start:
                        self.stop()
                        
                        self.first_start = False
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
                        time.sleep(3)
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1800, 1800, 1000, 1000])
                        time.sleep(3)
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1800, 1100, 1000, 1000])
                        time.sleep(3)
                        self.ppm.update_ppm_channels([1500, 1500, 1750, 1500, 1800, 1100, 1000, 1000])
                        print("gora")
                        time.sleep(2)
                        self.ppm.update_ppm_channels([1500, 1500, 1500, 1500, 1800, 1100, 1000, 1000])
                        print("stop")
                        """time.sleep(5)
                        self.ppm.update_ppm_channels([1800, 1500, 1500, 1500, 1800, 1100, 1000, 1000])
                        print("prawo")
                        time.sleep(3)
                        self.ppm.update_ppm_channels([1300, 1500, 1500, 1500, 1800, 1100, 1000, 1000])
                        print("lewo")
                        time.sleep(3)
                        self.ppm.update_ppm_channels([1500, 1500, 1500, 1500, 1800, 1100, 1000, 1000])   """

                        self.update_ppm = True
                        self.update_pids = True
                        self.start()
                    ax = self.rollPID.output_ppm 
                    if(int(self.rollPID.output_ppm) > 1510 or int(self.rollPID.output_ppm)< 1490):
                        ax += 250
                    vals = [int(ax), 1500, int(self.throttlePID.output_ppm), int(self.yawPID.output_ppm), 1800, 1100, 1000,
                            1000]
                    self.ppm.update_ppm_channels(vals)
                    #print(vals)
                    # int(self.yawPID.output_ppm)

            else:

                self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
                self.first_start = True

    def calculate_pids(self):
        if self.update_pids:
            self.yawPID.calculate()
            self.throttlePID.calculate()
            self.rollPID.calculate()
        else:
            self.yawPID.reset()
            self.rollPID.reset()
            self.throttlePID.reset()

    def update(self, mid, ratio):
        in_min = 0
        in_max = 1
        out_max = 1
        out_min = -1
        mid[0] = (mid[0] - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        mid[1] = -((mid[1] - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
        if mid[0] < 0:
            ratio *= -1
        self.yawPID.update(-mid[0])
        #self.rollPID.update(-ratio)
        self.throttlePID.update(-mid[1])

    def get_pid_values(self):
        values = []
        with open(os.path.join("settings", "pidValues.csv"), 'r') as fd:
            reader = csv.reader(fd)
            for row in reader:
                values.append(row)
        return values

    def update_P_I_D_values(self):
        values = self.get_pid_values()

        self.yawPID.Kp = float(values[0][0])
        self.yawPID.Ki = float(values[1][0])
        self.yawPID.Kd = float(values[2][0])

        self.rollPID.Kp = float(values[0][1])
        self.rollPID.Ki = float(values[1][1])
        self.rollPID.Kd = float(values[2][1])

        self.throttlePID.Kp = float(values[0][2])
        self.throttlePID.Ki = float(values[1][2])
        self.throttlePID.Kd = float(values[2][2])

    def write_to_file(self):
        line = str(self.yawPID.value) + "," + str(self.yawPID.output_ppm) + "," + str(self.rollPID.value) + "," + \
              str(self.rollPID.output_ppm) + "," + str(self.throttlePID.value) + "," + \
              str(self.throttlePID.output_ppm) + "\n"
        self.file.write(line)


class multiPIDs:
    def __init__(self, conn):
        self.child_conn = conn
        self._timer = None
        self.dt = ps.PID_PPM_UPDATE_TIME
        self.is_running = False
        if not Values.WINDOWS_TESTS:
            self.ppm = My_PPM()
        self.update_ppm = False
        self.update_pids = False
        self.first_start = True
        values = self.get_pid_values()

        self.yawPID = PID(ps.YAW_SETPOINT, 1000, 2000, float(values[0][0]), float(values[1][0]), float(values[2][0]))
        self.rollPID = PID(ps.ROLL_SETPOINT, 1000, 2000, float(values[0][1]), float(values[1][1]), float(values[2][1]))
        self.throttlePID = PID(ps.THROTTLE_SETPOINT, 1000, 2000, float(values[0][2]), float(values[1][2]), float(values[2][2]), start_from_min=True)

        self.last_yaw_ppm = 0
        self.last_roll_ppm = 0
        self.last_throttle_ppm = 0

        #pitchPID = PID(0.5, 1000, 2000, 1, 2, 3)

        if Values.WRITE_TO_FILE:
            self.file = open('inputs_outputs.csv', 'a')
        if not Values.WINDOWS_TESTS:
            self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
        self.start()

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.dt, self._run)
            self._timer.start()
            self.is_running = True

    def _run(self):
        self.is_running = False
        self.start()
        self.calculate_pids()
        self.send_ppm()
        if Values.WRITE_TO_FILE:
            self.write_to_file()

    def stop(self):
        self._timer.cancel()
        self.is_running = False
        self.update_ppm = False         ################## ??????????? moze cos byc  nie tak
        self.update_pids = False
        if not Values.WINDOWS_TESTS:
            self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
        if Values.WRITE_TO_FILE:
            self.file.close()

    def send_ppm(self):
        if not Values.WINDOWS_TESTS:
            if self.update_ppm:
                #
                if (int(self.throttlePID.output_ppm) != self.last_throttle_ppm) or \
                        (int(self.rollPID.output_ppm) != self.last_roll_ppm) or \
                        (int(self.yawPID.output_ppm) != self.last_yaw_ppm):

                    self.last_yaw_ppm = int(self.yawPID.output_ppm)
                    self.last_roll_ppm = int(self.rollPID.output_ppm)
                    self.last_throttle_ppm = int(self.throttlePID.output_ppm)

                    if self.first_start:
                        self.stop()
                        self.first_start = False
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
                        time.sleep(2)
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1800, 1800, 1000, 1000])
                        time.sleep(2)
                        self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1800, 1100, 1000, 1000])
                        time.sleep(2)
                        self.ppm.update_ppm_channels([1500, 1500, 1600, 1500, 1800, 1100, 1000, 1000])
                        time.sleep(2)
                        self.ppm.update_ppm_channels([1500, 1500, 1500, 1500, 1800, 1100, 1000, 1000])

                        self.update_ppm = True
                        self.update_pids = True
                        self.start()

                    vals = [int(self.rollPID.output_ppm), 1500, int(self.throttlePID.output_ppm), 1500, 1800, 1100, 1000, 1000]
                    self.ppm.update_ppm_channels(vals)

                    msg = "v" + str(self.last_yaw_ppm) + "," + str(self.last_roll_ppm) + "," + str(self.last_throttle_ppm)
                    self.child_conn.send(msg)
            else:

                if not self.first_start:
                    self.ppm.update_ppm_channels([1500, 1500, 1000, 1500, 1100, 1800, 1000, 1000])
                self.first_start = True

    def calculate_pids(self):
        if self.update_pids:
            self.yawPID.calculate()
            self.throttlePID.calculate()
            self.rollPID.calculate()
        else:
            self.yawPID.reset()
            self.rollPID.reset()
            self.throttlePID.reset()

    def update(self, mid, ratio):
        in_min = 0
        in_max = 1
        out_max = 1
        out_min = -1
        mid[0] = (mid[0] - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
        mid[1] = -((mid[1] - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

        self.yawPID.update(ratio)
        self.rollPID.update(mid[0])
        self.throttlePID.update(-mid[1])

    def get_pid_values(self):
        values = []
        with open(os.path.join("settings", "pidValues.csv"), 'r') as fd:
            reader = csv.reader(fd)
            for row in reader:
                values.append(row)
        return values

    def update_P_I_D_values(self):
        values = self.get_pid_values()

        self.yawPID.Kp = float(values[0][0])
        self.yawPID.Ki = float(values[1][0])
        self.yawPID.Kd = float(values[2][0])

        self.rollPID.Kp = float(values[0][1])
        self.rollPID.Ki = float(values[1][1])
        self.rollPID.Kd = float(values[2][1])

        self.throttlePID.Kp = float(values[0][2])
        self.throttlePID.Ki = float(values[1][2])
        self.throttlePID.Kd = float(values[2][2])

    def write_to_file(self):
        line = str(self.yawPID.value) + "," + str(self.yawPID.output_ppm) + "," + str(self.rollPID.value) + "," + \
              str(self.rollPID.output_ppm) + "," + str(self.throttlePID.value) + "," + \
              str(self.throttlePID.output_ppm) + "\n"
        self.file.write(line)