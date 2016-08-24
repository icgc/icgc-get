# icgc-get

This is the `icgc-get` utility, a universal download client for accessing ICGC data residing in various data repositories. 

## Motivation

The data for ICGC resides in many data repositories around the world. These repositories 
each have their own environment (public cloud, private cloud, on-premise file systems, etc.), 
access controls (DACO, OAuth, asymmetric keys, IP filtering), download clients and configuration mechanisms. 
Thus, there is much for a user to learn and perform before actually acquiring the data. 
This is compounded by the fact that the number of environments are increasing over time 
and their characteristics are frequently changing. A coordinated mechanism to bootstrap and 
streamline this process is highly desirable. This is the problem the `icgc-get` tool helps to solve.

## Installation

To install `icgc-get` on your local machine, first download the `icgc-get` package, then unzip the executable.
`unzip icgc-get_linux_v0.3.13_x64.zip`

Once the installation is complete, `icgc-get` can be invoked with the path to the `icgc-get` executable.  To make the
executable callable from anywhere, you need to either move the executable to a folder on your `PATH` or add the folder you downloaded
the executable to to the `PATH`.  You can find out what directories are on your path with `echo $PATH` on Mac and linux or `path` on Windows. You can
add folders to your path with `export PATH=$PATH:/folder` on Mac and Linux or `set PATH=%PATH%;/folder` on Windows.

`icgc-get` is capable of interfacing with the [ICGC storage client,](http://docs.icgc.org/cloud/guide/#installation) Genetorrent, 
[the GDC data transfer tool,](https://gdc.nci.nih.gov/access-data/gdc-data-transfer-tool) [the EGA download client](https://www.ebi.ac.uk/ega/about/your_EGA_account/download_streaming_client#download)
and [the Amazon Web Service command line interface.](http://docs.aws.amazon.com/cli/latest/userguide/installing.html)  
If you do not have any of download clients installed locally, `icgc-get` is capable of running them through
the ICGC get Docker container. Running any of the clients through the Docker container will prevent issues from arising related to conflicting 
software requirements for the data download clients. To enable this functionality, first [install 
Docker.](https://www.docker.com/products/overview) Make sure to create a [Docker group](https://docs.docker.com/v1.11/engine/installation/linux/ubuntulinux/#create-a-docker-group)
when running on a Linux machine to ensure that docker can be run without root permissions.

**This tool requires one or more download clients installed or docker installed to function**

##Quick start

After installing `icgc-get`, you will need to do configure some of the essential usage parameters,
such as your access credentials. Enter `./icgc-get configure` and follow the instructions of the prompts.
To keep the default values for the parameters, press enter.

For further information, please view our documentation [here.](http://docs.icgc.org/cloud/icgc-get/)

### Packaging from source

First run `pip install -r ~/requirements.txt` to ensure that all necessary packages have been installed. Then run:
 
``` 
python ~/pyinstaller.py --clean --onefile -n icgc-get --additional-hooks-dir ~/icgc-get/bin ~/icgc-get/icgcget/cli.py
```

The executable `icgc-get` will be in a folder named `dist` in your current directory.  Compress it into a zip fileoo, with the naming convention of 
`icgc-get_v$VERSION_$OS_x64.zip`


#### Packaging inside Docker

As an easy way to build a Linux version of icgc-get, you can package it inside the Docker container described in the icgc-get Dockerfile.
First rebuild the container to make sure all of the latest updates to the code are copied inside the table.  This command must
be run from the root directory of the icgc-get project.

```
docker build -t icgc/icgc-get:$VERSION .
```

Then run the container in interactive mode. You will need to mount a directory as a data volume to transfer the packaged icgc-get out of the Docker container.

```
docker run -it -v ~/mnt:/icgc/mnt icgc/icgc-get:$VERSION
```

Once inside, navigate to `/icgc/mnt`, and run the following version of the pyinstaller call:

```
python /icgc/pyinstaller/pyinstaller-pyinstaller-1804636/pyinstaller.py --clean --onefile -n icgc-get --additional-hooks-dir /icgc/icgcget/bin /icgc/icgcget/icgcget/cli.py
```
Then, exit Docker. Your executable will be present in the mounted directory, but the docker container does not natively have the ability to zip files.