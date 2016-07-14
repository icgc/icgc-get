# ICGC Get

This is the `icgc-get` utility, a universal download client for accessing ICGC data residing in various data repositories. 

## Movitation

The data for ICGC resides in many data repositories around the world. These repositories 
each have their own environment (public cloud, private cloud, on-premise file systems, etc.), 
access controls (DACO, OAuth, asymmetric keys, IP filtering), download clients and configuration mechanisms. 
Thus, there is much for a user to learn and perform before actually acquiring the data. 
This is compounded by the fact that the number of environments are increasing over time 
and their characteristics are frequently changing.  A coordinated mechanism to bootstrap and 
streamline this process is highly desirable. This is the problem the `icgc-get` helps to solve.

## Installation

To install ICGC get on your local machine , first download the ICGC get package, then unzip the executable.

Once the installation is complete, ICGC get can be invoked with the path to the `icgc-get` executable.  To make the
executable callable from anywhere, you need to either move the executable to a folder on your `PATH` or add the folder you downloaded
the executable to to the `PATH`.  You can find out what directories are on your path with `echo $PATH` on Mac and linux or `path` on windows.  You can
add folders to your path with `export PATH=$PATH:/folder` on Mac and Linux or `set PATH=%PATH%;/folder` on Windows

ICGC get is capable of interfacing with the [ICGC storage client,](http://docs.icgc.org/cloud/guide/#installation) Genetorrent, 
[the GDC data transfer tool,](https://gdc.nci.nih.gov/access-data/gdc-data-transfer-tool) [the EGA download client](https://www.ebi.ac.uk/ega/about/your_EGA_account/download_streaming_client#download)
and [the Amazon Web Service command line interface.](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)  If you do not have any of download clients installed locally, ICGC get is capable of running them through
the ICGC get Docker container. Running any of the clients through the Docker container will prevent issues from arising related to conflicting 
software requirements for the data download clients.  To enable this functionality, first [install 
Docker.](https://www.docker.com/products/overview)

**This tool requires one or more download clients or docker to be installed to function**

For further information, please view our documentation [here](http://docs.icgc.org/cloud/icgc-get/)