FROM alpine:edge

RUN apk update && apk add build-base libzmq musl-dev python3 python3-dev zeromq-dev py-pip

COPY . /sqlite_rx
WORKDIR /sqlite_rx

RUN pip install -U Cython
RUN pip install -r requirements.txt
RUN pip install -e .