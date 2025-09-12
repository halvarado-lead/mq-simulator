FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*

COPY Client/ibmmq-runtime_9.3.0.0_amd64.deb Client/ibmmq-client_9.3.0.0_amd64.deb Client/ibmmq-gskit_9.3.0.0_amd64.deb Client/ibmmq-sdk_9.3.0.0_amd64.deb /tmp/

RUN apt-get update && \
    apt-get install -y /tmp/ibmmq-runtime_9.3.0.0_amd64.deb && \
    apt-get install -y /tmp/ibmmq-gskit_9.3.0.0_amd64.deb && \
    apt-get install -y /tmp/ibmmq-client_9.3.0.0_amd64.deb && \
    apt-get install -y /tmp/ibmmq-sdk_9.3.0.0_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

ENV LD_LIBRARY_PATH=/opt/mqm/lib64:/opt/mqm/lib

RUN pip install pymqi

WORKDIR /app
COPY mq_producer.py mq_consumer.py data.json ./
CMD ["python", "mq_producer.py"]
