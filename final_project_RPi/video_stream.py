import numpy as np
import cv2
import sys
from multiprocessing import Process, Queue, Pool
import zmq
import base64
"""
python3 examples/semantic_segmentation.py \
  --model test_data/deeplabv3_mnv2_pascal_quant_edgetpu.tflite \
  --input test_data/bird.bmp \
  --keep_aspect_ratio \
  --output ${HOME}/segmentation_result.jpg
"""

import argparse
import time
import numpy as np
from PIL import Image

from pycoral.adapters import common
from pycoral.adapters import segment
from pycoral.utils.edgetpu import make_interpreter
from pycoral.adapters import classify
from pycoral.utils.dataset import read_label_file
from  testCheck import checkPIcam, executeandsearch
import os

class Classify_and_Stream:

    def create_pascal_label_colormap(self):
        """Creates a label colormap used in PASCAL VOC segmentation benchmark.
        Returns:
            A Colormap for visualizing segmentation results.
        """
        colormap = np.zeros((256, 3), dtype=int)
        indices = np.arange(256, dtype=int)

        for shift in reversed(range(8)):
            for channel in range(3):
                colormap[:, channel] |= ((indices >> channel) & 1) << shift
                indices >>= 3

        return colormap


    def label_to_color_image(self, label):
        """Adds color defined by the dataset colormap to the label.
        Args:
            label: A 2D array with integer type, storing the segmentation label.
        Returns:
            result: A 2D array with floating type. The element of the array
            is the color indexed by the corresponding element in the input label
            to the PASCAL color map.
        Raises:
            ValueError: If label is not of rank 2 or its value is larger than color
            map maximum entry.
        """
        if label.ndim != 2:
            raise ValueError('Expect 2-D input label')

        colormap = self.create_pascal_label_colormap()

        if np.max(label) >= len(colormap):
            raise ValueError('label value too large.')

        return colormap[label]

    def classify_and_stream(self, detected, prediction, queue:Queue, buffer_count=5):
        FIFO = '/home/pi/final_project/fifo'
        context = zmq.Context()
        footage_socket = context.socket(zmq.PUB)
        footage_socket.connect('tcp://localhost:5555')
        interpreter_seg = make_interpreter('/home/pi/rpi-face/deeplabv3_mnv2_pascal_quant_edgetpu.tflite', device=':0')
        interpreter_seg.allocate_tensors()
        width, height = common.input_size(interpreter_seg)
        
        if (checkPIcam('video0')):
            cap = cv2.VideoCapture(1)
        else:
            cap = cv2.VideoCapture(0)
        # counter for classification results:
        result_counter = [0,0,0]
        while(True):
            # Capture frame-by-frame
            ret, frame = cap.read()

            #convert opencv image to PIL image
            img = Image.fromarray(frame)

            #classification:
            labels = read_label_file('/home/pi/rpi-face/label_map.txt')

            interpreter = make_interpreter('/home/pi/rpi-face/retrained_model_edgetpu.tflite')
            interpreter.allocate_tensors()

            size = common.input_size(interpreter)
            image = img.resize(size, Image.ANTIALIAS)
            common.set_input(interpreter, image)

            start = time.perf_counter()
            interpreter.invoke()
            inference_time = time.perf_counter() - start
            classes = classify.get_classes(interpreter, 1, 0.0)
            #print('%.1fms' % (inference_time * 1000))

            #print('-------RESULTS--------')
            for c in classes:
                print('%s: %.5f' % (labels.get(c.id, c.id), c.score))

            # determine if door should be opened
            result_counter[c.id] += 1
            if (result_counter[c.id] >= buffer_count):
                result_counter[0] = 0
                result_counter[1] = 0
                result_counter[2] = 0
                prediction = labels.get(c.id, c.id)
                if (prediction == 'negative'):
                    detected = False
                else:
                    detected = True
            #print("write in queue")
            while (queue.qsize() > 2):
                queue.get(True)
            queue.put(detected)
            print(detected)
            print(prediction)
           # fifo = open(FIFO, 'w')
           # print("write in")
           # fifo.write(str(detected))
           # fifo.close()


            #start = time.perf_counter()
            # segmentation
            resized_img, _ = common.set_resized_input(
                interpreter_seg, img.size, lambda size: img.resize(size, Image.ANTIALIAS))
            start = time.perf_counter()
            interpreter_seg.invoke()

            result = segment.get_output(interpreter_seg)
            end = time.perf_counter()
            if len(result.shape) == 3:
                result = np.argmax(result, axis=-1)

            # If keep_aspect_ratio, we need to remove the padding area.
            new_width, new_height = resized_img.size
            result = result[:new_height, :new_width]
            mask_img = Image.fromarray(self.label_to_color_image(result).astype(np.uint8))
            #end = time.perf_counter()

            # Concat resized input image and processed segmentation results.
            output_img = Image.new('RGB', (2 * new_width, new_height))
            output_img.paste(resized_img, (0, 0))
            output_img.paste(mask_img, (width, 0))

            #end = time.perf_counter()
            seg_time = end - start 
            #print('segmentation time: %0.1fms' % (seg_time * 1000))
            #print('classification time: %.1fms' % (inference_time * 1000))


            #convert PIL image to opencv form
            open_cv_image = np.array(output_img)
            
            #frame = cv2.resize(open_cv_image, (640, 480))  # resize the frame
            encoded, buffer = cv2.imencode('.jpg', open_cv_image)
            jpg_as_text = base64.b64encode(buffer)
            footage_socket.send(jpg_as_text)

            # Display the resulting frame
            #cv2.imshow('frame', open_cv_image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # When everything done, release the capture
        cap.release()
        cv2.destroyAllWindows()
