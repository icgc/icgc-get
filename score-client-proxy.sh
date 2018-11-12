#!/bin/sh

##
# Set up inotifywatch to automatically chown any newly created file in the mount directory. The userid and groupid of the *host*
# mounted directory will be used for each new file. This gets around the problem where the storage client is run as root in the 
# Docker container, so files created are owned by root. If the host user doesn't have sudo privileges, then they won't be able to
# access the download and log files.
#
##
nohup inotifywait -q -m -r /icgc/mnt -e create --format '%w%f' | while read f; do chown $(stat -c '%u' /icgc/mnt):$(stat -c '%g' /icgc/mnt) $f; done &

/icgc/score-client/bin/score-client "$@"
