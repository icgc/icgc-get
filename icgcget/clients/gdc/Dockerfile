#    ______________________   ______     __
#   /  _/ ____/ ____/ ____/  / ____/__  / /_
#   / // /   / / __/ /      / / __/ _ \/ __/
# _/ // /___/ /_/ / /___   / /_/ /  __/ /_
#/___/\____/\____/\____/   \____/\___/\__/
# Banner @ http://goo.gl/VCY0tD

FROM       ubuntu:14.04
MAINTAINER ICGC <dcc-support@icgc.org>

ENV GDC_VERSION gdc-client_v1.0.1_Ubuntu14.04_x64
#
# Update apt, add FUSE support, requiered libraries and basic command line tools
#

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y libfuse-dev fuse software-properties-common && \
  apt-get install -y python-pip python-dev libffi-dev

#
# Install Oracle JDK 8 for icgc-storage client 
#

RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update && apt-get upgrade -y
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get install -y \
    oracle-java8-installer \
    oracle-java8-set-default
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle


#
# Install latest version of gdc download tool
#

RUN mkdir -p /icgc/gdc-data-transfer-tool && \
    cd /icgc/gdc-data-transfer-tool && \
    wget -qO- https://gdc.nci.nih.gov/files/public/file/$GDC_VERSION.zip -O temp.zip ; \
    unzip temp.zip -d /icgc/gdc-data-transfer-tool ; \
    rm temp.zip && \
    cd /icgc

ENV PATH=$PATH:/icgc/gdc-data-transfer-tool

#
# Set working directory for convenience with interactive usage
#


WORKDIR /icgc

#
# Set path defaults as environmental variables
#

ENV ICGCGET_GDC_PATH=/icgc/gdc-data-transfer-tool/gdc-client
