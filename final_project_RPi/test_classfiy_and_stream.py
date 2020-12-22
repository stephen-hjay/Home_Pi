from video_stream import Classify_and_Stream

prediction = ""
global detected
detected = False
test_class = Classify_and_Stream()
test_class.classify_and_stream(detected, prediction, 5)
