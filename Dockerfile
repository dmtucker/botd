FROM python:3.9
RUN pip install --upgrade pipenv
WORKDIR /botd
COPY . .
RUN pipenv install --deploy
ENTRYPOINT ["pipenv", "run", "python", "-m", "botd"]
