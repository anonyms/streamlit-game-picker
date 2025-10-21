FROM python:3.13-slim

WORKDIR /usr/src/app

# dont write pyc files
# dont buffer to stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# COPY ./requirements.txt /usr/src/app/requirements.txt
COPY ./requirements.txt .

# dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && rm -rf /root/.cache/pip