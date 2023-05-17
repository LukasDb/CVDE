FROM tensorflow/tensorflow:latest-gpu



COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

#WORKDIR /cvde
#COPY . /cvde
#RUN python -m pip install /cvde/.

WORKDIR /ws
