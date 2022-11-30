# welcome to copy-paste hell


import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image


def letterbox(im, new_shape=(640, 640), color=(114, 114, 114), auto=True, scaleup=True, stride=32):
    # Resize and pad image while meeting stride-multiple constraints
    shape = im.shape[:2]  # current shape [height, width]
    if isinstance(new_shape, int):
        new_shape = (new_shape, new_shape)

    # Scale ratio (new / old)
    r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
    if not scaleup:  # only scale down, do not scale up (for better val mAP)
        r = min(r, 1.0)

    # Compute padding
    new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
    dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

    if auto:  # minimum rectangle
        dw, dh = np.mod(dw, stride), np.mod(dh, stride)  # wh padding

    dw /= 2  # divide padding into 2 sides
    dh /= 2

    if shape[::-1] != new_unpad:  # resize
        im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)  # add border
    return im, r, (dw, dh)


class Detector:
    def __init__(self, model_path):
        providers = [
            'CUDAExecutionProvider',
            # 'CPUExecutionProvider'
        ]
        self.session = ort.InferenceSession(model_path, providers=providers)
        self.outname = [i.name for i in self.session.get_outputs()]
        self.inname = [i.name for i in self.session.get_inputs()]
        self.frame = None
        self.last_detection = [320, 240]

    def detect(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        image = img.copy()
        image, ratio, dwdh = letterbox(image, auto=False)
        image = image.transpose((2, 0, 1))
        image = np.expand_dims(image, 0)
        image = np.ascontiguousarray(image)

        im = image.astype(np.float32)
        im /= 255
        im.shape

        inp = {self.inname[0]:im}
        outputs = self.session.run(self.outname, inp)[0]

        ori_images = [img.copy()]

        # target position in px
        best_mid = None
        best_score = 0

        for i,(batch_id,x0,y0,x1,y1,cls_id,score) in enumerate(outputs):
            image = ori_images[int(batch_id)]
            box = np.array([x0,y0,x1,y1])
            box -= np.array(dwdh*2)
            box /= ratio
            box = box.round().astype(np.int32).tolist()
            cls_id = int(cls_id)
            score = round(float(score),3)
            
            if score > best_score:
                best_score = score
                best_mid = [(box[0]+box[2])/2, (box[1]+box[3])/2]
                cv2.rectangle(image,box[:2],box[2:],(0, 0, 255),2)
                cv2.putText(image,str(score),(box[0], box[1] - 2),cv2.FONT_HERSHEY_SIMPLEX,0.75,[225, 255, 255],thickness=2)  

        self.frame = ori_images[0]
        print(self.last_detection[0])
        if self.last_detection[0] < 0:
            const_out = [40, 240]
        if self.last_detection[0] > 0:
            const_out = [600, 240]
        if self.last_detection[0] == 0:
            const_out = [320, 240]
        const_out = [self.last_detection[0],240]
        best_mid = best_mid or const_out#self.last_detection
        self.last_detection = best_mid

        return (best_mid+[0,0], 1) if best_mid is not None else ([0, 0], 1)
