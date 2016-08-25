#    ______________________   ______     __
#   /  _/ ____/ ____/ ____/  / ____/__  / /_
#   / // /   / / __/ /      / / __/ _ \/ __/
# _/ // /___/ /_/ / /___   / /_/ /  __/ /_
#/___/\____/\____/\____/   \____/\___/\__/
# Banner @ http://goo.gl/VCY0tD

FROM       ubuntu:14.04
MAINTAINER ICGC <dcc-support@icgc.org>

ENV GT_VERSION 3.8.7
ENV GT_VERSION_LONG 207
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
# Install GeneTorrent and add to PATH
#


RUN mkdir -p /icgc/genetorrent && \
    cd /icgc/genetorrent && \
    wget -qO- https://annai.egnyte.com/dd/LWTWQGXeAi/ -O genetorrent-download.deb && \
    wget -qO- https://annai.egnyte.com/dd/Ixrj77etn2 -O genetorrent-common.deb && \
    apt-get install libboost-filesystem1.54.0 libboost-program-options1.54.0 libboost-regex1.54.0 libboost-system1.54.0 libxerces-c3.1 libxqilla6 python-support &&\
    dpkg -i ./genetorrent-common.deb && \
    dpkg -i ./genetorrent-download.deb

ENV PATH=$PATH:/icgc/genetorrent/bin




