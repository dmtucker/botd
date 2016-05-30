FROM python:2

RUN pip install --upgrade pip
RUN pip install pep8 pylint

WORKDIR /tmp
COPY requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /src
COPY . .
RUN pep8 botd setup.py
RUN pylint botd setup.py
RUN rm -rf dist
RUN ./setup.py sdist
RUN pip install dist/*

WORKDIR /
ENTRYPOINT ["botd"]
