from settings.settings import PIDSettings
import time


class PID:
    def __init__(self, set_point, pid_min, pid_max, Kp, Ki, Kd, start_from_min=False):
        self.dt = PIDSettings.PID_PPM_UPDATE_TIME
        self.Kp = float(Kp)
        self.Ki = float(Ki)
        self.Kd = float(Kd)
        self.set_point = float(set_point)
        self.time = time.time()
        self.max = pid_max
        self.min = pid_min
        self.last_e = None
        self.sum_e = 0
        self.value = None
        self.output_ppm = (self.max + self.min) / 2
        if start_from_min:
            self.output_ppm = self.min
        self.start_output_ppm = self.output_ppm

    def update(self, v):
        self.value = v

    def reset(self):
        self.value = self.set_point
        self.output_ppm = self.start_output_ppm
        self.last_e = None
        self.sum_e = 0

    def calculate(self):
        if self.value is not None:
            e = self.set_point - self.value

            if self.last_e is not None:
                D = - self.Kd * (e - self.last_e) / self.dt
            else:
                D = 0

            self.sum_e += (e * self.dt * self.Ki)

            if self.sum_e > PIDSettings.PID_I_MAX:
                self.sum_e = PIDSettings.PID_I_MAX
            if self.sum_e < - PIDSettings.PID_I_MAX:
                self.sum_e = - PIDSettings.PID_I_MAX

            I = self.sum_e

            #self.output = self.Kp * (e + D + I)
            PID_sum = self.Kp * e + D + I

            self.last_e = e

            output_ppm = self.start_output_ppm + PID_sum

            if output_ppm > self.max:
                output_ppm = self.max
            if output_ppm < self.min:
                output_ppm = self.min

            self.output_ppm = output_ppm
