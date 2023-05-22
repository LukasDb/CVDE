FROM tensorflow/tensorflow:latest-gpu

#RUN groupadd -r cvde && useradd -r -m -g cvde cvde
#USER cvde

RUN export PATH=$PATH:$HOME/.local/bin

WORKDIR $HOME/CVDE

COPY . .
#COPY requirements.txt .
RUN pip install -r requirements.txt

RUN pip install .