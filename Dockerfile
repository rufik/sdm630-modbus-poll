FROM python:3.7-alpine3.10

LABEL Description="Utility to read SDM630 V2 Modbus power meters and publish metrics to MQTT."

#RUN apk update && apk --no-cache add build-base git libtool autoconf automake cmake pkgconf linux-headers mosquitto-clients

RUN echo "Installing required python packages"
RUN pip3 install pymodbus apscheduler paho-mqtt tzlocal
RUN echo "Copying script..."
COPY src/sdm630_to_mqtt.py /app/sdm630_to_mqtt.py
RUN echo "Done."

CMD ["python3", "/app/sdm630_to_mqtt.py"]
