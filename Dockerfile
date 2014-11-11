FROM ubuntu:14.04
MAINTAINER harlo <harlo.holmes@gmail.com>

# UPDATE
RUN apt-get update
RUN apt-get install -yq wget nginx zip unzip openjdk-7-jre-headless openssl

# ADD OUR PRIMARY USER
RUN useradd -ms /bin/bash -p $(openssl passwd -1 narnia) harlo
RUN adduser harlo sudo

# ADD FILES GALORE
ADD . /home/harlo/test_package
RUN chown -R harlo:harlo /home/harlo
USER harlo
ENV HOME /home/harlo
WORKDIR /home/harlo/test_package

EXPOSE 22 443