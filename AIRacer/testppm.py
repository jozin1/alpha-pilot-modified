from PPM.PPM import My_PPM
import time
ppm = My_PPM()


while True:
    ppm.update_ppm_channels([1400, 1100, 1100, 1100, 1800, 1100, 1500, 1500])
    time.sleep(1)
    
    