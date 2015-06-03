FROM debian:latest
MAINTAINER David Tucker <david.tucker@isilon.com>

ADD etc /root/etc
ADD botd.py /root/botd.py
RUN chmod +x /root/botd.py

CMD ["/root/botd.py /root/etc/*"]
