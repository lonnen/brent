FROM python:3.13-slim

RUN apt update && apt-get install gcc -y

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
COPY ./requirements.txt /requirements.txt

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

COPY ./brent /brent

WORKDIR /brent

CMD ["python","-u","main.py"]