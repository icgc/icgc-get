# ICGC Get
Universal download client for ICGC data residing in various environments. 

## Installing the Python Script

The python script can be installed by simply navigating to the `icgc-get` directory and running the command:

```shell
python setup.py install
```

## Using the Python Script

The syntax for calling the python client is
```shell
icgc-get --config [CONFIG] download [REPO] [FILEIDS] [OPTIONS]
```

The first required for the python script are the repository or repositories that are being targeted for download.
Valid repositories are:

| Code             | Repository                     |
| --------         | -------------------------------|
| `aws-virginia`   | Amazon Web Services            |
| `collaboratory`  | Collaboratory                  |
| `ega`            | European Genome Association    |
| `gdc`            | Genomic data commons           |
| `cghub`          | Cancer genomic hub             |
| `pdc`            | Bionimbus protected data cloud |

Prepend each repository with the `-r`, for example `-r aws-virginia -r ega`.  The repositories will be processed with priority corresponding to theorder they are specified
Second you must specify an ICGC File id or manifest file id corresponding to the file you wish to download. If this is for a manifest file append the tags `-m` or `--manifest`.  This will specify the file or files to be downloaded.  **The EGA repository does not currently support
downloads using a manifest file.**  It is possible to specify multiple file ID's when downloading from the
gdc or cghub repositories.  **The EGA and ICGC repositories do not currently support this functionality**

If not running the tool in a docker container, a user must also specify the `--output` where files are to be saved
and the `--config`, the location of the configuration file.  **Absolute paths are required for both arguments.**

## Using the Docker Container

First, pull the docker image using the command

`docker pull icgc/icgc-get`

To save some typing, you can add a convenience bash alias to make working with the container easier:

```shell
alias icgc-get="docker run -it --rm -v {MNT_DIR}:/icgc/mnt icgc/icgc-get --config /icgc/mnt/config.yaml"
```

replacing `{PATH}` with the path to your mounted directory. This directory will be populated by the script with
process logs and downloaded files.


This will enable the invocation of the python script with the command `icgc-get`.  When running through the docker container there is no
need to use the `--output` or `--config` arguments.

Then execute the command as normal:

```shell
icgc-get download FI378424 -r  collaboratory
```


to do a status check on the same files
```shell
icgc-get status FI378424 -r collaboratory
```

Sample output

```
╒══════════════════════╤════════╤════════╤══════════════╤═══════════════╕
│                      │   Size │ Unit   │   File Count │   Donor_Count │
╞══════════════════════╪════════╪════════╪══════════════╪═══════════════╡
│ collaboratory: total │ 197.44 │ KB     │            1 │              1│
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ collaboratory: StGV  │ 197.44 │ KB     │            1 │              1│
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ cghub: total         │   3.94 │ GB     │            2 │              2│
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ cghub: Aligned Reads │   3.94 │ GB     │            1 │              2│
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ Total                │   3.94 │ GB     │            3 │              3│
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ StGV                 │ 197.44 │ KB     │            1 │             1 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ Aligned Reads        │  3.94  │ GB     │            2 │             2 │
╘══════════════════════╧════════╧════════╧══════════════╧═══════════════╛
Valid access to the Collaboratory.
Valid access to the cghub files.
```

To check the version of all clients used by ICGC Get
```
icgc-get version
```
Sample output
```
AWS CLI Version: 1.10.34
GDC Client Version v0.7
EGA Client Version: 2.2.2
Gtdownload Release 3.8.7
ICGC Storage Client Version: 1.0.13
ICGC-Get Version: 0.5
```
## Unit Tests

Unit tests have been provided in the tests directory of the repository.  They require a configuration file with valid
EGA and cghub credentials to be saved in the root of the repository.

To run unit tests, execute the following:

```shell
python setup.py test
```
