from flask import Flask, Response
from picamera2 import Picamera2
from libcamera import controls
import cv2
import time
import numpy as np

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
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (FRAME_WIDTH, FRAME_HEIGHT), 'format': 'YUV420'})
picam2.configure(config)
picam2.set_controls({
    #"AfMode": controls.AfModeEnum.Manual,
    #"LensPosition": 0.0,
    #"ColourGains": (1.75, 1.45),
    #"Contrast": 2.0,
    # "NoiseReductionMode": draft.NoiseReductionModeEnum.HighQuality,
    "AeEnable": False,
    "ExposureTime": 200000,   # microseconds (20ms)
    "AnalogueGain": 0.9,
    "AwbEnable": False
})

picam2.start()


def detect_refraction_edge(gray_img):
    roi_strip = gray_img[200:300, :] # A 100-pixel tall strip in the middle
    profile = np.mean(roi_strip, axis=0)
    gradient = np.gradient(profile)
    edge_pixel_index = np.argmax(gradient)
    
    return edge_pixel_index


# Sub-pixel enhancement (Optional but recommended)
def get_subpixel_edge(frame):
    profile = np.mean(frame[200:300, :], axis=0)
    gradient_profile = np.gradient(profile)
    initial_idx = np.argmax(gradient_profile)
    # Fits a parabola to the peak and its two neighbors for 0.1 pixel accuracy
    if initial_idx <= 0 or initial_idx >= len(gradient_profile) - 1:
        return float(initial_idx)

    y1, y2, y3 = gradient_profile[initial_idx-1:initial_idx+2]
    denom = 2 * (y1 - 2 * y2 + y3)
    if denom == 0: 
        return float(initial_idx)

    offset = (y1 - y3) / denom
    return initial_idx + offset


def generate_frames():
    while True:
        frame = picam2.capture_array()

        # Optional: draw ROI rectangle for alignment
        #cv2.rectangle(frame, (100, 100), (500, 400), (0, 255, 0), 2)
        frame = frame[ROI_Y:(ROI_Y+ROI_HEIGHT), ROI_X:(ROI_X+ROI_WIDTH)]
        for x in range(int(ROI_WIDTH / 100)):
            cv2.putText(frame, '|' + str(x), (x * 100, ROI_HEIGHT - 30), font, scale, colour, 1)

        cv2.putText(frame, 'Refraction edge: ' + str(detect_refraction_edge(frame)), (0, 30), font, scale, colour, 2)

        refined_pixel_pos = get_subpixel_edge(frame)
        cv2.putText(frame, 'Refined position: ' + str(refined_pixel_pos)[:6], (0, 60), font, scale, colour, 2)
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

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


