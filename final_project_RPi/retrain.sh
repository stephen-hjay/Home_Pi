ImgPath=/home/pi/face_images/
ModelPath=/home/pi/rpi-face/mobilenet_v1_1.0_224_quant_embedding_extractor_edgetpu.tflite
OutputPath=/home/pi/rpi-face/

python3 coral_retrain.py \
      --data_dir $ImgPath \
      --embedding_extractor_path $ModelPath \
      --output_dir $OutputPath
