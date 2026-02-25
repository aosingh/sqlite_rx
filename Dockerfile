FROM python:3-slim AS base

ARG USERNAME=sqliteuser
ARG UID=1001
ARG GID=1001
ARG HOME_DIR=/home/${USERNAME}

# Upgrade OS packages
RUN set -ex \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create the group and user
RUN groupadd --gid ${GID} ${USERNAME} \
    && useradd -m -u ${UID} -g ${GID} -d ${HOME_DIR} -s /bin/bash ${USERNAME}

RUN chown ${USER_NAME}:${USERNAME} ${HOME_DIR}

FROM base AS builder
COPY . /sqlite_rx

WORKDIR /svc

RUN pip install --upgrade pip
RUN pip install Cython
RUN pip install wheel && pip wheel --wheel-dir=/svc/wheels /sqlite_rx[cli]
RUN rm -rf /sqlite_rx


FROM base

COPY --from=builder /svc /svc
WORKDIR /svc

RUN pip install --upgrade pip
RUN pip install --no-index /svc/wheels/*.whl

USER ${USERNAME}
WORKDIR ${HOME_DIR}
