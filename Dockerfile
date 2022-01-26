FROM python:3.9
RUN pip install --upgrade pipenv
WORKDIR /botd
COPY . .
RUN pipenv install --deploy
RUN pipenv check
ENTRYPOINT ["pipenv", "run", "botd"]
