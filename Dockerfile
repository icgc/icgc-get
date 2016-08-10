#    ______________________   ______     __
#   /  _/ ____/ ____/ ____/  / ____/__  / /_
#   / // /   / / __/ /      / / __/ _ \/ __/
# _/ // /___/ /_/ / /___   / /_/ /  __/ /_
#/___/\____/\____/\____/   \____/\___/\__/
# Banner @ http://goo.gl/VCY0tD

FROM       ubuntu:14.04
MAINTAINER ICGC <dcc-support@icgc.org>

ENV EGA_VERSION 2.2.2
ENV GT_VERSION 3.8.7
ENV GT_VERSION_LONG 207
ENV GDC_VERSION gdc-client_v1.0.1_Ubuntu14.04_x64
#
# Update apt, add FUSE support, requiered libraries and basic command line tools
#

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y libfuse-dev fuse software-properties-common && \
  apt-get install -y python-pip python-dev libffi-dev && \
  apt-get install -y libicu52 && \
# Required for Genetorrent and Icgc
  apt-get install -y  openssl libssl-dev
# Required to download Genetorrent

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
# Download and install latest EGA download client version
#

ENV PATH=$PATH:/icgc/genetorrent/bin
RUN mkdir -p /icgc/ega-download-demo && \
    apt-get install -y unzip curl wget && \
    cd /icgc/ega-download-demo && \
    wget -qO- https://www.ebi.ac.uk/ega/sites/ebi.ac.uk.ega/files/documents/EgaDemoClient_$EGA_VERSION.zip -O temp.zip ; \
    unzip temp.zip -d /icgc/ega-download-demo

#
# Install GeneTorrent and add to PATH
#

RUN mkdir -p /icgc/genetorrent && \
    cd /icgc/genetorrent && \
    wget -qO- https://annai.egnyte.com/dd/LWTWQGXeAi/ -O genetorrent-download.deb && \
    wget -qO- https://annai.egnyte.com/dd/Ixrj77etn2 -O genetorrent-common.deb && \
    apt-get install libboost-filesystem1.54.0 libboost-program-options1.54.0 libboost-regex1.54.0 libboost-system1.54.0 libxerces-c3.1 libxqilla6 python-support &&\
    dpkg -i ./genetorrent-common.deb && \
    dpkg -i ./genetorrent-download.deb

# 
# Install latest version of storage client distribution
#

RUN mkdir -p /icgc/icgc-storage-client && \
    cd /icgc/icgc-storage-client && \
    wget -qO- https://artifacts.oicr.on.ca/artifactory/dcc-release/org/icgc/dcc/icgc-storage-client/[RELEASE]/icgc-storage-client-[RELEASE]-dist.tar.gz | \
    tar xvz --strip-components 1 && \
    mkdir -p /icgc/icgc-storage-client/logs

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

COPY . /icgc/icgcget/
COPY ./logback.xml /icgc/icgc-storage-client/conf

#
# Install ICGC-get and make root directory, install aws-cli, cleanup pip
#

RUN cd /icgc/icgcget && \
    wget -qO- https://github.com/pyinstaller/pyinstaller/zipball/develop -O temp.zip ; \
    unzip temp.zip -d /icgc/pyinstaller && \
    apt-get upgrade -y && \
    pip install -U pip setuptools && \
    pip install awscli && \
    pip uninstall -y pip setuptools && \
    mkdir /icgc/mnt


WORKDIR /icgc

#
# Set path defaults as environmental variables
#

ENV ICGCGET_ICGC_PATH=/icgc/icgc-storage-client/bin/icgc-storage-client
ENV ICGCGET_GDC_PATH=/icgc/gdc-data-transfer-tool/gdc-client
ENV ICGCGET_EGA_PATH=/icgc/ega-download-demo/EgaDemoClient.jar
ENV ICGCGET_GNOS_PATH=/usr/bin/gtdownload
ENV ICGCGET_PDC_PATH=/usr/local/bin/aws
ENV ICGCGET_CONFIG=/icgc/mnt/config.yaml
