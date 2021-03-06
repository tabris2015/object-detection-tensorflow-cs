from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import io
import re
import time

from annotation import Annotator

import numpy as np
import cv2
# import picamera

from PIL import Image
from tflite_runtime.interpreter import Interpreter

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


def load_labels(path):
    """Loads the labels file. Supports files with or without index numbers."""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        labels = {}
        for row_number, content in enumerate(lines):
            pair = re.split(r"[:\s]+", content.strip(), maxsplit=1)
            if len(pair) == 2 and pair[0].strip().isdigit():
                labels[int(pair[0])] = pair[1].strip()
            else:
                labels[row_number] = pair[0].strip()
    return labels


def set_input_tensor(interpreter, image):
    """Sets the input tensor."""
    tensor_index = interpreter.get_input_details()[0]["index"]
    input_tensor = interpreter.tensor(tensor_index)()[0]
    input_tensor[:, :] = image


def get_output_tensor(interpreter, index):
    """Returns the output tensor at the given index."""
    output_details = interpreter.get_output_details()[index]
    tensor = np.squeeze(interpreter.get_tensor(output_details["index"]))
    return tensor


def detect_objects(interpreter, image, threshold):
    """Returns a list of detection results, each a dictionary of object info."""
    set_input_tensor(interpreter, image)
    interpreter.invoke()

    # Get all output details
    boxes = get_output_tensor(interpreter, 0)
    classes = get_output_tensor(interpreter, 1)
    scores = get_output_tensor(interpreter, 2)
    count = int(get_output_tensor(interpreter, 3))

    results = []
    for i in range(count):
        if scores[i] >= threshold:
            result = {
                "bounding_box": boxes[i],
                "class_id": classes[i],
                "score": scores[i],
            }
            results.append(result)
    return results


def annotate_objects(annotator, results, labels):
    """Draws the bounding box and label for each object in the results."""
    for obj in results:
        # Convert the bounding box figures from relative coordinates
        # to absolute coordinates based on the original resolution
        ymin, xmin, ymax, xmax = obj["bounding_box"]
        xmin = int(xmin * CAMERA_WIDTH)
        xmax = int(xmax * CAMERA_WIDTH)
        ymin = int(ymin * CAMERA_HEIGHT)
        ymax = int(ymax * CAMERA_HEIGHT)

        # Overlay the box, label, and score on the camera preview
        annotator.bounding_box([xmin, ymin, xmax, ymax])
        annotator.text(
            [xmin, ymin], "%s\n%.2f" % (labels[obj["class_id"]], obj["score"])
        )


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--model", help="File path of .tflite file.", required=True)
    parser.add_argument("--labels", help="File path of labels file.", required=True)
    parser.add_argument(
        "--threshold",
        help="Score threshold for detected objects.",
        required=False,
        type=float,
        default=0.4,
    )
    args = parser.parse_args()

    labels = load_labels(args.labels)
    interpreter = Interpreter(args.model)
    interpreter.allocate_tensors()
    _, input_height, input_width, _ = interpreter.get_input_details()[0]["shape"]

    scale = 0.4

    video = cv2.VideoCapture('videos/rubber.mp4')
    # annotator = Annotator(camera)
    dim = (320, 320)

    while video.isOpened():
        ret, img = video.read()
        if not ret:
            print('end!')
            break
        frame = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
        start_time = time.monotonic()
        results = detect_objects(interpreter, frame, args.threshold)
        elapsed_ms = (time.monotonic() - start_time) * 1000
        # print(results, elapsed_ms)
        for obj in results:
            ymin, xmin, ymax, xmax = obj["bounding_box"]
            xmin = int(xmin * input_width)
            xmax = int(xmax * input_width)
            ymin = int(ymin * input_height)
            ymax = int(ymax * input_height)
            frame = cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255 ,255), 2)
            print(f'{labels[obj["class_id"]]} {obj["score"]} {obj["bounding_box"]}')
        # annotator.clear()
        # annotate_objects(annotator, results, labels)
        # annotator.text([5, 0], "%.1fms" % (elapsed_ms))
        # annotator.update()
        # out.write(frame)
        cv2.imshow('video',frame)
        # time.sleep(0.1)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # with picamera.PiCamera(
    #     resolution=(CAMERA_WIDTH, CAMERA_HEIGHT), framerate=30
    # ) as camera:
    #     camera.start_preview()
    #     try:
    #         stream = io.BytesIO()
    #         annotator = Annotator(camera)
    #         for _ in camera.capture_continuous(
    #             stream, format="jpeg", use_video_port=True
    #         ):
    #             stream.seek(0)
    #             image = (
    #                 Image.open(stream)
    #                 .convert("RGB")
    #                 .resize((input_width, input_height), Image.ANTIALIAS)
    #             )
    #             start_time = time.monotonic()
    #             results = detect_objects(interpreter, image, args.threshold)
    #             elapsed_ms = (time.monotonic() - start_time) * 1000

    #             annotator.clear()
    #             annotate_objects(annotator, results, labels)
    #             annotator.text([5, 0], "%.1fms" % (elapsed_ms))
    #             annotator.update()

    #             stream.seek(0)
    #             stream.truncate()

    #     finally:
    #         camera.stop_preview()


if __name__ == "__main__":
    main()
