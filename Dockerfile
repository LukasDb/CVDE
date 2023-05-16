FROM tensorflow/tensorflow:latest-gpu


# Install CVDE (deactivated for now)
#WORKDIR /cvde
#COPY . /cvde
#RUN python -m pip install /cvde/.

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

WORKDIR /ws
