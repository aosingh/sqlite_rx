FROM python:3.13-slim as base

WORKDIR /svc

COPY . /svc

RUN pip install --upgrade pip pipx && pipx install uv
RUN uv venv && uv sync --extra cli
RUN ln -s .venv/bin/sqlite* bin/ 

