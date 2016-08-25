#    ______________________   ______     __
#   /  _/ ____/ ____/ ____/  / ____/__  / /_
#   / // /   / / __/ /      / / __/ _ \/ __/
# _/ // /___/ /_/ / /___   / /_/ /  __/ /_
#/___/\____/\____/\____/   \____/\___/\__/
# Banner @ http://goo.gl/VCY0tD

FROM       ubuntu:14.04
MAINTAINER ICGC <dcc-support@icgc.org>

ENV EGA_VERSION 2.2.2

#
# Update apt, add FUSE support, requiered libraries and basic command line tools
#

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y libfuse-dev fuse software-properties-common && \
  apt-get install -y python-pip python-dev libffi-dev

#
# Install Oracle JDK 8 for icgc storage client, ega
#

RUN add-apt-repository ppa:webupd8team/java
RUN apt-get update && apt-get upgrade -y
RUN echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | /usr/bin/debconf-set-selections
RUN apt-get install -y \
    oracle-java8-installer \
    oracle-java8-set-default
ENV JAVA_HOME /usr/lib/jvm/java-8-oracle

#
# Download and install latest EGA download client version
#


RUN mkdir -p /icgc/ega-download-demo && \
    apt-get install -y unzip curl wget && \
    cd /icgc/ega-download-demo && \
    wget -qO- https://www.ebi.ac.uk/ega/sites/ebi.ac.uk.ega/files/documents/EgaDemoClient_$EGA_VERSION.zip -O temp.zip ; \
    unzip temp.zip -d /icgc/ega-download-demo


WORKDIR /icgc





