FROM debian:latest
ADD botd.json /root/botd.json
ADD botd.py /root/botd.py
RUN chmod +x /root/botd.py
RUN apt-get update
RUN apt-get install -y python python-pip python-dev python-lxml
RUN pip install feedparser twisted twython
CMD ["/root/botd.py /root/botd.json"]
