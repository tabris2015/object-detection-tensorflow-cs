FROM nvcr.io/nvidia/tensorflow:21.02-tf2-py3
RUN echo 'hola'
# protoc package
ENV PROTOC_ZIP=protoc-3.14.0-linux-x86_64.zip
RUN curl -OL https://github.com/protocolbuffers/protobuf/releases/download/v3.14.0/$PROTOC_ZIP
RUN unzip -o $PROTOC_ZIP -d /usr/local bin/protoc
RUN unzip -o $PROTOC_ZIP -d /usr/local 'include/*'
RUN rm -f $PROTOC_ZIP
# install dependencies
RUN pip install tensorflow-datasets matplotlib pandas imageio
WORKDIR /app
RUN git clone --depth 1 https://github.com/tensorflow/models
WORKDIR /app/models/research/
# install tensorflow object detection API
RUN protoc object_detection/protos/*.proto --python_out=.
RUN cp object_detection/packages/tf2/setup.py .
RUN python -m pip install .
WORKDIR /app
# download ssd mobilenet
RUN wget http://download.tensorflow.org/models/object_detection/tf2/20200711/ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.tar.gz
RUN tar -xf ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8.tar.gz
RUN if [ -d "models/research/object_detection/test_data/checkpoint" ]; then rm -Rf models/research/object_detection/test_data/checkpoint; fi
RUN mkdir models/research/object_detection/test_data/checkpoint
RUN mv ssd_mobilenet_v2_fpnlite_320x320_coco17_tpu-8/checkpoint models/research/object_detection/test_data/


ENTRYPOINT [ "jupyter", "notebook" ]