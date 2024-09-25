FROM faust.cs.fau.de:5000/floppcraft-deps
WORKDIR /
COPY . .

ENV FLASK_APP=src/backend.py
ENV FLASK_RUN_HOST=::
ENV FLASK_RUN_PORT=5001

EXPOSE 5001
CMD ["flask", "run"]
