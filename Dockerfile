FROM python:2

RUN pip install --upgrade pip

WORKDIR /src
COPY . .
RUN rm -rf dist
RUN ./setup.py sdist
RUN pip install dist/*

WORKDIR /
ENTRYPOINT ["botd"]
