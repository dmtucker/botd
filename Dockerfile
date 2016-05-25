FROM python:2

RUN pip install --upgrade pip
RUN pip install pep8 pylint

WORKDIR /src
COPY . .
RUN pep8 botd setup.py
RUN pylnt botd setup.py
RUN rm -rf dist
RUN python setup.py sdist
RUN pip install dist/*
WORKDIR /

ENTRYPOINT ["botd"]
