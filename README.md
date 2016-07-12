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

Once the installation is complete, ICGC get can be invoked with the path to the `icgc-get` executable.

If you do not have any of download clients installed locally, ICGC get is capable of running them through Docker. 
Running any of the clients through a Docker container will prevent issues from arising related to conflicting 
software requirements for the data download clients.  To enable this functionality, first [install 
Docker.](https://www.docker.com/products/overview)

For further information, please view our documentation [here](http://docs.icgc.org/cloud/icgc-get/)