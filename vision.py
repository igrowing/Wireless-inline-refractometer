import cv2
import copy
import numpy as np
from libcamera import controls
from picamera2 import Picamera2

FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
ROI_X = 0
ROI_Y = 250
ROI_WIDTH = FRAME_WIDTH
ROI_HEIGHT = 700

class Vision:

    colour = (255, 255, 255)
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1

    def __init__(self):
        self.frame = None
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(main={"size": (FRAME_WIDTH, FRAME_HEIGHT), 'format': 'YUV420'})
        self.picam2.configure(config)
        self.picam2.set_controls({
            "AeEnable": False,
            "ExposureTime": 200000,  # microseconds (20ms)
            "AnalogueGain": 0.9,
            "AwbEnable": False
        })

        self.picam2.start()


    def take_picture(self):
        frame = self.picam2.capture_array()
        frame = frame[ROI_Y:(ROI_Y + ROI_HEIGHT), ROI_X:(ROI_X + ROI_WIDTH)]
        self.frame = frame


    def put_labels(self, labels_list):
        frame = copy.deepcopy(self.frame)
        for x in range(int(ROI_WIDTH / 100)):
            cv2.putText(frame, '|' + str(x), (x * 100, ROI_HEIGHT - 30), self.font, self.scale, self.colour, 1)

        left_labels = len(labels_list) // 2
        counter = 0
        for text, value in labels_list:
            # Align left labels to the left and the rest to the right
            if counter < left_labels:
                cv2.putText(frame, f'{text}: {str(value)}', (0, (counter + 1) * 30), self.font, self.scale, self.colour, 2)
            else:
                label = f'{text}: {str(value)}'
                (text_width, text_height), baseline = cv2.getTextSize(label, self.font, self.scale, 2)
                x_position = FRAME_WIDTH - text_width - 10  # 10px right margin
                cv2.putText(frame, label, (x_position, (counter - left_labels + 1) * 30), self.font, self.scale, self.colour, 2)

            counter += 1

            if 'edge' in text.lower():
                x_position = int(value)
                cv2.line(frame, (x_position, 350), (x_position, FRAME_HEIGHT - 20), (200, 200, 200), 1)

        _, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()