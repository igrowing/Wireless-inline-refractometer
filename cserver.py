#!/usr/bin/env python3
import cv2
import time
import vision
import signal
import asyncio
# import numpy as np
import refractometer
# from libcamera import controls
# from picamera2 import Picamera2
from flask import Flask, Response


app = Flask(__name__)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

rm = loop.run_until_complete(refractometer.Refractometer.get_instance())
vis = vision.Vision()


def generate_frames():
    while True:
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

        time.sleep(1)  # 1 FPS


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

def shutdown_handler(signum, frame):
    print("Signal received, shutting down...")
    loop.run_until_complete(rm.shutdown())
    loop.stop()
    exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host='0.0.0.0', port=5000)


