from settings.settings import Values, Constants, PIDSettings
import importlib.util
import cv2
import numpy as np


class Detector:
    def __init__(self, model_path):

        if Values.WINDOWS_GPU:
            import tensorflow as tf
            self.interpreter = tf.lite.Interpreter(model_path=model_path)

        else:
            pkg = importlib.util.find_spec('tflite_runtime')
            if pkg:
                from tflite_runtime.interpreter import Interpreter
                if Values.USE_EDGE_TPU:
                    from tflite_runtime.interpreter import load_delegate
            else:
                from tensorflow.lite.python.interpreter import Interpreter
                if Values.USE_EDGE_TPU:
                    from tensorflow.lite.python.interpreter import load_delegate
            if Values.USE_EDGE_TPU:
                self.interpreter = Interpreter(model_path=model_path,
                                               experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
            else:
                self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        self.height = self.input_details[0]['shape'][1]
        self.width = self.input_details[0]['shape'][2]
        self.img_ind = 0
        print("Model init success!")
        
        self.frame = cv2.imread("../images/start.jpg")

    def detect(self, frame):
        image = cv2.resize(frame, (self.width, self.height))
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        input_data = np.expand_dims(image_rgb, axis=0)
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        boxes = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        classes = self.interpreter.get_tensor(self.output_details[1]['index'])[0]
        scores = self.interpreter.get_tensor(self.output_details[2]['index'])[0]

        height, width, channels = frame.shape
        good_scores = []
        good_boxes = []
        good_classes = []
        for i in range(len(scores)):
            if (scores[i] > Values.DETECTION_THRESHOLD) and (scores[i] <= 1.0):
                ymin = int(max(1, (boxes[i][0] * height)))
                xmin = int(max(1, (boxes[i][1] * width)))
                ymax = int(min(height, (boxes[i][2] * height)))
                xmax = int(min(width, (boxes[i][3] * width)))
                good_boxes.append(boxes[i])
                good_scores.append(scores[i])
                good_classes.append(classes[i])

                object_name = ""
                object_class = int(classes[i])

                hsv = np.uint8([[[61 + (object_class-2)*25, 255, 255]]])
                rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
                col = (int(rgb[0][0][0]), int(rgb[0][0][1]), int(rgb[0][0][2]))

                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), col, 2)

                if object_class == Constants.GATE:
                    object_name = "Gate"
                elif object_class == Constants.RD:
                    object_name = "RD"
                elif object_class == Constants.RU:
                    object_name = "RU"
                elif object_class == Constants.LD:
                    object_name = "LD"
                elif object_class == Constants.LU:
                    object_name = "LU"

                label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                label_ymin = max(ymin, labelSize[1] + 10)

                cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10),
                              (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
                cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        mid, ratio = self.check_detections(good_boxes, good_classes, good_scores)
        if mid is None:
            in_min = -1
            in_max = 1
            out_max = 1
            out_min = 0
            a = (PIDSettings.THROTTLE_SETPOINT - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
            b = ((PIDSettings.ROLL_SETPOINT - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
            mid = [a, b]

        if ratio is None:
            ratio = PIDSettings.YAW_SETPOINT
        cv2.circle(frame, (int(mid[0] * width), int(mid[1] * height)), 15, (0, 0, 255), 2)
        self.frame = frame
        return mid, ratio

    def check_detections(self, boxes, classes, scores):
        LD = -1
        LU = -1
        RD = -1
        RU = -1
        Gate = -1
        LD_score = 0
        LU_score = 0
        RD_score = 0
        RU_score = 0
        Gate_score = 0
        corners = 0
        Corners_score = 0
        mid = None
        width = None
        height = None
        sides_ratio = None

        for i in range(len(scores)):
            if classes[i] == Constants.LD:
                if scores[i] > LD_score:
                    LD = i
                    LD_score = scores[i]
            elif classes[i] == Constants.LU:
                if scores[i] > LU_score:
                    LU = i
                    LU_score = scores[i]
            elif classes[i] == Constants.RD:
                if scores[i] > RD_score:
                    RD = i
                    RD_score = scores[i]
            elif classes[i] == Constants.RU:
                if scores[i] > RU_score:
                    RU = i
                    RU_score = scores[i]
            elif classes[i] == Constants.GATE:
                if scores[i] > Gate_score:
                    Gate = i
                    Gate_score = scores[i]

        if LD_score != 0:
            Corners_score += LD_score
            corners += 1
        if LU_score != 0:
            Corners_score += LU_score
            corners += 1
        if RD_score != 0:
            Corners_score += RD_score
            corners += 1
        if RU_score != 0:
            Corners_score += RU_score
            corners += 1
        if corners != 0:
            Corners_score /= corners

        """Wszystkie możliwosci katow"""

        if Gate_score == 0 and Corners_score == 0:
            return None, None

        if Gate_score >= Corners_score or (Gate_score != 0 and corners == 1):
            max_y = boxes[Gate][2]
            min_y = boxes[Gate][0]
            max_x = boxes[Gate][3]
            min_x = boxes[Gate][1]
            mid = [min_x + (max_x - min_x) / 2, min_y + (max_y - min_y) / 2]

            if corners == 4:
                width = (boxes[RU][3] + boxes[RD][3]) / 2 - (boxes[LU][1] + boxes[LD][1]) / 2
                height = (boxes[LD][2] + boxes[RD][2]) / 2 - (boxes[RU][0] + boxes[LU][0]) / 2
                print("4444")
            elif corners == 3:
                print("3333")
                if LD == -1:
                    y_min = (boxes[LU][0] + boxes[RU][0]) / 2
                    y_max = boxes[RD][2]
                    x_max = (boxes[RU][3] + boxes[RD][3]) / 2
                    x_min = boxes[LU][1]
                    width = x_max - x_min
                    height = y_max - y_min
                    
                elif LU == -1:
                    y_min = boxes[RU][0]
                    y_max = (boxes[LD][2] + boxes[RD][2]) / 2
                    x_max = (boxes[RU][3] + boxes[RD][3]) / 2
                    x_min = boxes[LD][1]
                    width = x_max - x_min
                    height = y_max - y_min

                elif RU == -1:
                    y_min = boxes[LU][0]
                    y_max = (boxes[LD][2] + boxes[RD][2]) / 2
                    x_max = boxes[RD][3]
                    x_min = (boxes[LD][1] + boxes[LU][1]) / 2
                    width = x_max - x_min
                    height = y_max - y_min
                elif RD == -1:
                    y_min = (boxes[LU][0] + boxes[RU][0]) / 2
                    y_max = boxes[LD][2]
                    x_max = boxes[RU][3]
                    x_min = (boxes[LD][1] + boxes[LU][1]) / 2
                    width = x_max - x_min
                    height = y_max - y_min
                    
            elif corners == 2:
                if LD == -1 and RU == -1:
                    print("2222")
                    x_min = boxes[LU][1]
                    x_max = boxes[RD][3]
                    y_min = boxes[LU][0]
                    y_max = boxes[RD][2]
                    width = x_max - x_min
                    height = y_max - y_min
                elif LU == -1 and RD == -1:
                    print("2222")
                    x_min = boxes[LD][1]
                    x_max = boxes[RU][3]
                    y_min = boxes[RU][0]
                    y_max = boxes[LD][2]
                    width = x_max - x_min
                    height = y_max - y_min

        elif Gate_score == 0 and corners == 1:
            if LU != -1:
                mid = [boxes[LU][3], boxes[LU][2]]
            elif LD != -1:
                mid = [boxes[LD][3], boxes[LD][0]]
            elif RD != -1:
                mid = [boxes[RD][1], boxes[RD][0]]
            elif RU != -1:
                mid = [boxes[RU][1], boxes[RU][2]]
            return mid, 1

        else:
            if corners == 4:
                points = [(boxes[LU][1], boxes[LU][0]), (boxes[LD][1], boxes[LD][2]), (boxes[RU][3], boxes[RU][0]),
                          (boxes[RD][3], boxes[RD][2])]
                mid = np.mean(points, axis=0)
                width = (boxes[RU][3] + boxes[RD][3]) / 2 - (boxes[LU][1] + boxes[LD][1]) / 2
                height = (boxes[LD][2] + boxes[RD][2]) / 2 - (boxes[RU][0] + boxes[LU][0]) / 2
            elif corners == 3:
                if LD == -1:
                    y_min = (boxes[LU][0] + boxes[RU][0]) / 2
                    y_max = boxes[RD][2]
                    y = (y_max + y_min) / 2
                    x_max = (boxes[RU][3] + boxes[RD][3]) / 2
                    x_min = boxes[LU][1]
                    x = (x_max + x_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min
                elif LU == -1:
                    y_min = boxes[RU][0]
                    y_max = (boxes[LD][2] + boxes[RD][2]) / 2
                    y = (y_max + y_min) / 2
                    x_max = (boxes[RU][3] + boxes[RD][3]) / 2
                    x_min = boxes[LD][1]
                    x = (x_max + x_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min

                elif RU == -1:
                    y_min = boxes[LU][0]
                    y_max = (boxes[LD][2] + boxes[RD][2]) / 2
                    y = (y_max + y_min) / 2
                    x_max = boxes[RD][3]
                    x_min = (boxes[LD][1] + boxes[LU][1]) / 2
                    x = (x_max + x_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min
                elif RD == -1:
                    y_min = (boxes[LU][0] + boxes[RU][0]) / 2
                    y_max = boxes[LD][2]
                    y = (y_max + y_min) / 2
                    x_max = boxes[RU][3]
                    x_min = (boxes[LD][1] + boxes[LU][1]) / 2
                    x = (x_max + x_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min
            elif corners == 2:
                if LD == -1 and LU == -1:
                    y_min = boxes[RU][0]
                    y_max = boxes[RD][2]
                    y = (y_max + y_min) / 2
                    x = ((boxes[RU][3] + boxes[RD][3]) / 2) - (
                                y_max - y_min) / 2 * Values.CAMERA_HEIGHT / Values.CAMERA_WIDTH
                    mid = [x, y]
                    width = (y_max - y_min) * Values.CAMERA_HEIGHT / Values.CAMERA_WIDTH
                    height = y_max - y_min
                elif RD == -1 and RU == -1:
                    y_min = boxes[LU][0]
                    y_max = boxes[LD][2]
                    y = (y_max + y_min) / 2
                    x = ((boxes[LU][1] + boxes[LD][1]) / 2) + (
                                y_max - y_min) / 2 * Values.CAMERA_HEIGHT / Values.CAMERA_WIDTH
                    mid = [x, y]
                    width = (y_max - y_min) * Values.CAMERA_HEIGHT / Values.CAMERA_WIDTH
                    height = y_max - y_min
                elif LD == -1 and RD == -1:
                    x_min = boxes[LU][1]
                    x_max = boxes[RU][3]
                    x = (x_max + x_min) / 2
                    y = ((boxes[LU][0] + boxes[RU][0]) / 2) + (
                                x_max - x_min) / 2 / Values.CAMERA_HEIGHT * Values.CAMERA_WIDTH
                    mid = [x, y]
                    width = x_max - x_min
                    height = (x_max - x_min) * Values.CAMERA_WIDTH / Values.CAMERA_HEIGHT
                elif LU == -1 and RU == -1:
                    x_min = boxes[LD][1]
                    x_max = boxes[RD][3]
                    x = (x_max + x_min) / 2
                    y = ((boxes[LD][2] + boxes[RD][2]) / 2) - (
                                x_max - x_min) / 2 / Values.CAMERA_HEIGHT * Values.CAMERA_WIDTH
                    mid = [x, y]
                    width = x_max - x_min
                    height = (x_max - x_min) / Values.CAMERA_HEIGHT * Values.CAMERA_WIDTH
                elif LD == -1 and RU == -1:
                    x_min = boxes[LU][1]
                    x_max = boxes[RD][3]
                    x = (x_max + x_min) / 2
                    y_min = boxes[LU][0]
                    y_max = boxes[RD][2]
                    y = (y_max + y_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min
                elif LU == -1 and RD == -1:
                    x_min = boxes[LD][1]
                    x_max = boxes[RU][3]
                    x = (x_max + x_min) / 2
                    y_min = boxes[RU][0]
                    y_max = boxes[LD][2]
                    y = (y_max + y_min) / 2
                    mid = [x, y]
                    width = x_max - x_min
                    height = y_max - y_min

        if height is not None and width is not None:
            height *= Values.CAMERA_HEIGHT
            width *= Values.CAMERA_WIDTH
            sides_ratio = height - width

            if height >= width:
                sides_ratio /= height
            else:
                sides_ratio /= width
                
            if sides_ratio > 1:
                sides_ratio = 1
            elif sides_ratio < -1:
                sides_ratio = -1
        print("hw ", height, width)
        if mid is not None:
            if mid[0] > 1:
                mid[0] = 1
            elif mid[0] < 0:
                mid[0] = 0

            if mid[1] > 1:
                mid[1] = 1
            elif mid[1] < 0:
                mid[1] = 0

        return mid, sides_ratio
