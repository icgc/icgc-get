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
#
# Update apt, add FUSE support, requiered libraries and basic command line tools
#

RUN \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y libfuse-dev fuse curl wget software-properties-common && \
  apt-get install libicu52 && \
# Required for Genetorrent and Icgc
  apt-get install unzip
# Required to download EGA

#
# Install OpenSSL for Genetorrent
#

RUN apt-get install openssl

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
# Install python 2.7 and dependancies for Genetorrent and icgc-get.
#

RUN apt-get install -y python-pip && \
    pip install -U pip setuptools

COPY . /icgc/icgcget/
COPY /conf/ /icgc/conf

RUN cd /icgc/icgcget && \
    pip install -r requirements.txt && \
    python setup.py install

#
# Download and install latest EGA download client version
#

RUN mkdir -p /icgc/ega-download-demo && \
    cd /icgc/ega-download-demo && \
    wget -qO- https://www.ebi.ac.uk/ega/sites/ebi.ac.uk.ega/files/documents/EgaDemoClient_$EGA_VERSION.zip -O temp.zip ; \
    unzip temp.zip -d /icgc/ega-download-demo; \
    rm temp.zip

#
# Install GeneTorrent and add to PATH
#

RUN mkdir -p /icgc/genetorrent && \
    cd /icgc/genetorrent && \
    wget -qO- https://cghub.ucsc.edu/software/downloads/GeneTorrent/$GT_VERSION/GeneTorrent-download-$GT_VERSION-$GT_VERSION_LONG-Ubuntu14.04.x86_64.tar.gz | \
    tar xvz --strip-components 1 
ENV PATH=$PATH:/icgc/genetorrent/bin

# 
# Install latest version of storage client distribution
#

RUN mkdir -p /icgc/icgc-storage-client && \
    cd /icgc/icgc-storage-client && \
    wget -qO- https://seqwaremaven.oicr.on.ca/artifactory/dcc-release/org/icgc/dcc/icgc-storage-client/[RELEASE]/icgc-storage-client-[RELEASE]-dist.tar.gz | \
    tar xvz --strip-components 1

#
# Install latest version of gdc download tool
#

RUN mkdir -p /icgc/gdc-data-transfer-tool && \
    cd /icgc/gdc-data-transfer-tool && \
    wget -qO- https://gdc.nci.nih.gov/files/public/file/gdc-clientv07ubuntu1404x64_1.zip -O temp.zip ; \
    unzip temp.zip -d /icgc/gdc-data-transfer-tool ; \
    rm temp.zip && \
    cd /icgc

#
# Set working directory for convenience with interactive usage
#

WORKDIR /icgc

ENTRYPOINT ["icgc-get"]
