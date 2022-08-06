FROM python:3.10.1-slim as base

COPY . /sqlite_rx

WORKDIR /svc

RUN pip install --upgrade pip
RUN pip install Cython
RUN pip install wheel && pip wheel --wheel-dir=/svc/wheels /sqlite_rx[cli]
RUN rm -rf /sqlite_rx


FROM python:3.10.1-slim

COPY --from=base /svc /svc
WORKDIR /svc

RUN pip install --upgrade pip
RUN pip install --no-index /svc/wheels/*.whl