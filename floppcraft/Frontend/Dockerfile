FROM faust.cs.fau.de:5000/floppcraft-deps
WORKDIR /
COPY . .

ENV FLASK_APP=src/server.py
ENV FLASK_RUN_HOST=::

EXPOSE 5000
CMD ["flask", "run"]
