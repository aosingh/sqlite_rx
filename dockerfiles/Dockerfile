FROM python:3.11.0a5-alpine as base

WORKDIR /svc

RUN apk update && apk add build-base libzmq musl-dev zeromq-dev

RUN pip install --upgrade pip
RUN pip install Cython
RUN pip install wheel && pip wheel --wheel-dir=/svc/wheels sqlite_rx


FROM python:3.11.0a5-alpine
RUN apk update && apk add libzmq

COPY --from=base /svc /svc
WORKDIR /svc

RUN pip install --upgrade pip
RUN pip install --no-index --find-links=/svc/wheels sqlite_rx

