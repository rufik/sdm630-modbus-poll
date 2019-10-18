FROM alpine:3.10

LABEL Description="Eclipse Mosquitto MQTT Broker for armhf"

RUN echo "Installing required packages"
RUN apk update && apk --no-cache add build-base git libtool autoconf automake cmake pkgconf linux-headers mosquitto-clients

RUN echo "Building libmodbus now"
RUN cd ~
RUN git clone https://github.com/stephane/libmodbus.git
RUN cd libmodbus
RUN ls -al
RUN ./autogen.sh && ./configure
RUN make && make install

RUN echo "Building mbpoll now"
RUN cd ~
RUN git clone https://github.com/epsilonrt/mbpoll.git
RUN cd mbpoll
RUN ls -al
RUN mkdir build
RUN cd build
RUN cmake .. && make && make install

RUN echo "Done, cleaning up"
RUN cd ~
RUN rm -rf libmodbus/ mbpoll/
RUN apk del build-base git libtool autoconf automake cmake pkgconf linux-headers

VOLUME ["/app/script"]
CMD ["/bin/sh", "-c", "tail -f /dev/null"]
