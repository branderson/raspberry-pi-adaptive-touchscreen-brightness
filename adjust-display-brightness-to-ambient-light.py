#!/usr/bin/env python3

from picamera2 import Picamera2

import libcamera
import cv2
import subprocess
import numpy as np
from time import sleep
from datetime import datetime

BRIGHTNESS_MAX=255
BRIGHTNESS_MID=128
BRIGHTNESS_LOW=64
BRIGHTNESS_MIN=32
BRIGHTNESS_OFF=0

BRIGHTNESS_HUMAN_MID=255
BRIGHTNESS_HUMAN_LOW=255
BRIGHTNESS_HUMAN_MIN=128

AMBIENT_MAX=90
AMBIENT_MID=70
AMBIENT_LOW=10
AMBIENT_MIN=1


def capture_ambient_brightness(camera):
    array = camera.capture_array("main")
    pixAverage = np.average(array[...,1])
    #print ("Average ambient brightness: {:.1f}".format(pixAverage))
    return pixAverage

def detect_human(camera, human_detector):
    # TODO: Use opencv like https://github.com/raspberrypi/picamera2/blob/main/examples/opencv_face_detect.py
    # This doesn't appear to be working yet

    im = camera.capture_array()
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    humans = human_detector.detectMultiScale(grey, 1.1, 5)

    for (x, y, w, h) in humans:
        cv2.rectangle(im, (x, y), (x + w, y + h), (0, 255, 0))
        cv2.imwrite('/root/detections/' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.jpg', im)
        print("Human detected at ({}, {}, {}, {})".format(x, y, w, h))
        subprocess.run(["echo", "Human detected at ({}, {}, {}, {})".format(x, y, w, h)])
    if type(humans) is tuple:
        return False
    if humans.size:
        #subprocess.run(["echo", "Human Detected"])
        return True
    return False

def set_display_brightness(brightness):
    #print ("Setting brightness to {:.1f}".format(brightness))
    subprocess.run(["/root/set_display_brightness.sh", str(brightness)], check=True)

def main():
    with Picamera2() as camera:
        config = camera.create_still_configuration(main={"format": "XRGB8888", "size": (640, 480)}, transform=libcamera.Transform(hflip=1, vflip=1))
        camera.configure(config)
        camera.start()

        human_detector = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml")
        #human_detector = cv2.CascadeClassifier("/usr/share/opencv4/haarcascades/haarcascade_upperbody.xml")
        #cv2.startWindowThread()

        sleep(2)
        subprocess.run(["echo", "Camera Ready"])

        while True:
            try:
                brightness = capture_ambient_brightness(camera)
                human_detected = detect_human(camera, human_detector)
                if human_detected:
                    if brightness > AMBIENT_MID:
                        set_display_brightness(BRIGHTNESS_HUMAN_MID)
                    elif brightness > AMBIENT_LOW:
                        set_display_brightness(BRIGHTNESS_HUMAN_LOW)
                    else:
                        set_display_brightness(BRIGHTNESS_HUMAN_MIN)
                else:
                    if brightness > AMBIENT_MAX:
                        set_display_brightness(BRIGHTNESS_MAX)
                    elif brightness > AMBIENT_MID:
                        set_display_brightness(BRIGHTNESS_MID)
                    elif brightness > AMBIENT_LOW:
                        set_display_brightness(BRIGHTNESS_LOW)
                    elif brightness > AMBIENT_MIN:
                        set_display_brightness(BRIGHTNESS_MIN)
                    else:
                        set_display_brightness(BRIGHTNESS_OFF)
            except KeyboardInterrupt:
                print("\nExiting ..")
                break
            sleep(5)

if __name__ == "__main__": main()
