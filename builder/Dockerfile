FROM ubuntu:16.04
MAINTAINER ICGC <dcc-support@icgc.org>

RUN apt update && \
    apt install -y python2.7 python-pip lsb-core wget git python-dev

RUN pip install pyinstaller

COPY ./scripts/run.sh /icgc/run.sh
RUN chmod 755  /icgc/run.sh
    
# Requires the env variable REPO_MOUNT_PATH, GIT_BRANCH, USE_LOCAL, OUTPUT_DIR
CMD /icgc/run.sh
