#!/usr/bin/env python3
import cv2
import time
import vision
import numpy as np
import refractometer
from libcamera import controls
from picamera2 import Picamera2
from flask import Flask, Response


FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
ROI_X = 0
ROI_Y = 250
ROI_WIDTH = FRAME_WIDTH
ROI_HEIGHT = 700
colour = (255, 255, 255)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1

app = Flask(__name__)
rm = refractometer.Refractometer()
vis = vision.Vision()
# picam2 = Picamera2()
# config = picam2.create_preview_configuration(main={"size": (FRAME_WIDTH, FRAME_HEIGHT), 'format': 'YUV420'})
# picam2.configure(config)
# picam2.set_controls({
#     "AeEnable": False,
#     "ExposureTime": 200000,   # microseconds (20ms)
#     "AnalogueGain": 0.9,
#     "AwbEnable": False
# })
#
# picam2.start()

def generate_frames():
    while True:
        # frame = picam2.capture_array()
        #
        # # Optional: draw ROI rectangle for alignment
        # #cv2.rectangle(frame, (100, 100), (500, 400), (0, 255, 0), 2)
        # frame = frame[ROI_Y:(ROI_Y+ROI_HEIGHT), ROI_X:(ROI_X+ROI_WIDTH)]
        # for x in range(int(ROI_WIDTH / 100)):
        #     cv2.putText(frame, '|' + str(x), (x * 100, ROI_HEIGHT - 30), font, scale, colour, 1)
        #
        # cv2.putText(frame, 'Refraction edge: ' + str(detect_refraction_edge(frame)), (0, 30), font, scale, colour, 2)
        #
        # refined_pixel_pos = get_subpixel_edge(frame)
        # cv2.putText(frame, 'Refined position: ' + str(refined_pixel_pos)[:6], (0, 60), font, scale, colour, 2)
        # _, buffer = cv2.imencode('.jpg', frame)
        # frame_bytes = buffer.tobytes()

        vis.take_picture()
        rm.calculate(vis.frame)
        labels = [
            ("Visual alc. reading (%)", rm.visual_alcohol),
            ("Alcohol (%)", rm.alcohol),
            ("Sugar (%)", rm.sugar),
            ("Salt (%)", rm.salt),
            ("Edge detected (px)", rm.edge_pixel),
            ("Liquid temperature (C)", rm.temp_liquid),
            ("Air temperature (C)", rm.temp_ambient),
            ("Tube temperature (C)", rm.temp_tube),
        ]
        frame_bytes = vis.put_labels(labels)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.5)  # 2 FPS

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '''
    <html>
        <body>
            <h1>Camera Preview</h1>
            <img src="/video">
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


