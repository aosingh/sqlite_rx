FROM pypy:3-slim

RUN apt-get update
RUN apt-get -y install g++
RUN apt-get -y install libzmq3-dev

COPY . /sqlite_rx
WORKDIR /sqlite_rx

RUN pypy3 -m pip install -r requirements.txt
RUN pypy3 setup.py install