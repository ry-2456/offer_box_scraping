FROM python:3.8

ENV PYTHONUNBUFFERED=1 TZ=Asia/Tokyo

RUN mkdir /workdir

WORKDIR /workdir

ADD requirements.txt /workdir/

RUN pip3 install -r requirements.txt

CMD ["python", "offer_box.py"]
