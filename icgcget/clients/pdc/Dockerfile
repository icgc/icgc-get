#    ______________________   ______     __
#   /  _/ ____/ ____/ ____/  / ____/__  / /_
#   / // /   / / __/ /      / / __/ _ \/ __/
# _/ // /___/ /_/ / /___   / /_/ /  __/ /_
#/___/\____/\____/\____/   \____/\___/\__/
# Banner @ http://goo.gl/VCY0tD

FROM       ubuntu:14.04
MAINTAINER ICGC <dcc-support@icgc.org>

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
# Set working directory for convenience with interactive usage, copy icgc-get for development purposes
#

WORKDIR /icgc

#
# Install aws-cli, cleanup pip
#

RUN apt-get upgrade -y && \
    pip install -U pip setuptools && \
    pip install awscli && \
    pip uninstall -y pip setuptools && \
    mkdir /icgc/mnt



