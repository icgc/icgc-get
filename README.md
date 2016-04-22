# ICGC Download Client
Universal download client for ICGC data residing in various environments. 

## Installing the Python Script

The python script can be installed by simply navigating to the `icgc-download-client` directory and running the command:

```shell
python setup.py install
```

## Using the Python Script

The required arguments for the python script are the repository that is being targeted for download.
Valid repositories are:

* `aws` _(Amazon Web Services)_
* `collab` _(Collabratory)_
* `ega` _(European Genome Association)_
* `gdc` _(Genomic data commons)_
* `cghub` _(Cancer genomic hub)_

Second you must specify either a file id using the tag `-f` or `--file`, a manifest file using the tags `-m` or `--manifest`
or both.  This will specify the file or files to be downloaded.  **The EGA repository does not currently support
downloads using a manifest file.**  It is possible to specify multiple file ID's using the `-f` flag when downloading from the
gdc or cghub repositories.  **The EGA and ICGC repositories do not support this functionality**

If not running the tool in a docker container, a user must also specify the `--output` where files are to be saved
and the `--config`, the location of the configuration file.  **Absolute paths are required for both arguments.**

## Using the Docker Container

First, pull the docker image using the command

`docker pull icgc/icgc-download-client`

To save some typing, you can add a convenience bash alias to make working with the container easier:

```shell
alias icgc-download-client="docker run -it --rm -v {PATH}/icgc-download-client/mnt:/icgc/mnt icgc-download-client"
```

replacing `{PATH}` with the path to your mounted directory.  This directory must contain three subdirectories:
 * an empty`downloads` directory.
 * a `conf` directory containing the config.yaml file.
 * an empty logs directory`logs`.

This will enable the invocation of the python script with the command `icgc-download-client`.  When running through the docker container there is no
 need to use the `--output` or `--config` arguments.

Then execute the command as normal:

```shell
icgc-download-client collab -f  FI378424
```

#### Manifest files in the docker container

Because manifest files need to be accessible by the clients to be parsed, they should be saved in the directory being mounted.
Once you have saved them in your mounted directory, you will need to provided the path to the manifest file starting from the `/icgc/mnt` directory, so it can be found in the docker client filesystem


#### Unit tests

Unit tests have been provided in the tests directory of the repository.  They require a configuration file with valid
EGA and cghub credentials to be saved in the root of the repository.  They also require the command
`export $PYTHONPATH = {PATH}/lib/cli` to be entered prior to running unit tests.  To run unit tests, simply enter
`py.test` in the test directory



