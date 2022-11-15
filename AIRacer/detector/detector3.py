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

                if object_class == Constants.CORNERS:
                    object_name = "Corner"
                elif object_class == Constants.GATE:
                    object_name = "Gate"


                label = '%s: %d%%' % (object_name, int(scores[i] * 100))
                labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                label_ymin = max(ymin, labelSize[1] + 10)

                cv2.rectangle(frame, (xmin, label_ymin - labelSize[1] - 10),
                              (xmin + labelSize[0], label_ymin + baseLine - 10), (255, 255, 255), cv2.FILLED)
                cv2.putText(frame, label, (xmin, label_ymin - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        mid, ratio = self.check_detections(good_boxes, good_classes, good_scores, frame)
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

    def check_detections(self, boxes, classes, scores, frame):
        Gate = -1
        Gate_score = 0
        corners = []
        best_corners = []
        corners_scores = []
        corners_score = 0
        mid = None
        width = None
        height = None
        sides_ratio = None

        for i in range(len(scores)):
            if classes[i] == Constants.CORNERS:
                corners.append(i)
                corners_scores.append(scores[i])

            elif classes[i] == Constants.GATE:
                if scores[i] > Gate_score:
                    Gate = i
                    Gate_score = scores[i]

        c_s = corners_scores[:]
        c_s.sort()
        for i in range(len(c_s)):
            if i == 4:
                break
            else:
                ind = corners_scores.index(c_s[i])
                corners_scores[ind] = 0
                best_corners.append(corners[ind])
                corners_score += c_s[i]
        if len(best_corners) >0:
            corners_score /= len(best_corners)

        if Gate_score == 0 and corners_score == 0:
            return None, None

        if Gate_score >= corners_score or (Gate_score != 0 and len(best_corners) == 1):
            max_y = boxes[Gate][2]
            min_y = boxes[Gate][0]
            max_x = boxes[Gate][3]
            min_x = boxes[Gate][1]
            mid = [min_x + (max_x - min_x) / 2, min_y + (max_y - min_y) / 2]

            if len(best_corners) == 4:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]), (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]), (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c2 = [(boxes[best_corners[2]][3], boxes[best_corners[2]][2]), (boxes[best_corners[2]][1], boxes[best_corners[2]][0])]
                c3 = [(boxes[best_corners[3]][3], boxes[best_corners[3]][2]), (boxes[best_corners[3]][1], boxes[best_corners[3]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)
                c2 = np.mean(c2, axis=0)
                c3 = np.mean(c3, axis=0)

                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])
                y.append(c2[1])
                y.append(c3[1])

                x.append(c0[0])
                x.append(c1[0])
                x.append(c2[0])
                x.append(c3[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)

                width = x_max - x_min
                height = y_max - y_min

            elif len(best_corners) == 3:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]), (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]), (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c2 = [(boxes[best_corners[2]][3], boxes[best_corners[2]][2]), (boxes[best_corners[2]][1], boxes[best_corners[2]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)
                c2 = np.mean(c2, axis=0)

                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])
                y.append(c2[1])

                x.append(c0[0])
                x.append(c1[0])
                x.append(c2[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)

                width = x_max - x_min
                height = y_max - y_min

            elif len(best_corners) == 2:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]),
                      (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]),
                      (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)

                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])

                x.append(c0[0])
                x.append(c1[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)

                if (x_max - x_min)/x_max > 0.1 and (y_max - y_min)/x_max > 0.1:

                    width = x_max - x_min
                    height = y_max - y_min

        elif Gate_score == 0 and len(best_corners) == 1:

            return None, None

        else:
            if len(best_corners) == 4:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]), (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]), (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c2 = [(boxes[best_corners[2]][3], boxes[best_corners[2]][2]), (boxes[best_corners[2]][1], boxes[best_corners[2]][0])]
                c3 = [(boxes[best_corners[3]][3], boxes[best_corners[3]][2]), (boxes[best_corners[3]][1], boxes[best_corners[3]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)
                c2 = np.mean(c2, axis=0)
                c3 = np.mean(c3, axis=0)
                points = [c0, c1, c2, c3]
                mid = np.mean(points, axis=0)
                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])
                y.append(c2[1])
                y.append(c3[1])

                x.append(c0[0])
                x.append(c1[0])
                x.append(c2[0])
                x.append(c3[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)

                width = x_max - x_min
                height = y_max - y_min

            elif len(best_corners) == 3:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]), (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]), (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c2 = [(boxes[best_corners[2]][3], boxes[best_corners[2]][2]), (boxes[best_corners[2]][1], boxes[best_corners[2]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)
                c2 = np.mean(c2, axis=0)

                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])
                y.append(c2[1])

                x.append(c0[0])
                x.append(c1[0])
                x.append(c2[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)
                mid = [(x_min+x_max)/2, (y_min+y_max)/2]

                width = x_max - x_min
                height = y_max - y_min

            elif len(best_corners) == 2:
                c0 = [(boxes[best_corners[0]][3], boxes[best_corners[0]][2]),
                      (boxes[best_corners[0]][1], boxes[best_corners[0]][0])]
                c1 = [(boxes[best_corners[1]][3], boxes[best_corners[1]][2]),
                      (boxes[best_corners[1]][1], boxes[best_corners[1]][0])]
                c0 = np.mean(c0, axis=0)
                c1 = np.mean(c1, axis=0)

                y = []
                x = []

                y.append(c0[1])
                y.append(c1[1])

                x.append(c0[0])
                x.append(c1[0])

                x_max = max(x)
                x_min = min(x)
                y_max = max(y)
                y_min = min(y)

                if (x_max - x_min)/x_max > 0.1 and (y_max - y_min)/x_max > 0.1:

                    mid = [(x_min + x_max) / 2, (y_min + y_max) / 2]
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
