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

Prepend each repository with the `-r`, for example `-r aws-virginia -r ega`.  The repositories will be processed 
with priority corresponding to the order they are specified.  Second you must specify an ICGC File id or manifest 
file id corresponding to the file you wish to download. If this is for a manifest file append the tags `-m` 
or `--manifest`.  This will specify the file or files to be downloaded.  **The EGA repository does not currently support
downloads using a manifest file.**  It is possible to specify multiple file ID's individually instead of using manifest 
files for multiple downloads.

The download command comes with an automatic prompt that warns the user if the projected download size approaches the 
total available space in the download directory.  It is possible to supress this warning using the `-y` flag.


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

## Status
Another useful subcommand is `status`.  This takes the same primary inputs as `download`,
but instead of downloading the specified files, it will provide a list of all files that are
about to be downloaded, including their size, data type, and the repository they are hosted on.
It will also provide a summary of the download by repository and data type, showing how many files
and the total size of the files for each catagory.  In case of very large downloads, the individual
file summary may be too large to be practical, and it can be supressed with the flag `-nf`. 


To do a status check on the same files
```shell
icgc-get status FI378424 -r collaboratory
```

Sample output

```
╒══════════╤════════╤════════╤═══════════════╤═══════════════╤═══════════════╕
│          │   Size │ Unit   │ File Format   │ Data Type     │ Repo          │
╞══════════╪════════╪════════╪═══════════════╪═══════════════╪═══════════════╡
│ FI99996  │   3.52 │ GB     │ BAM           │ Aligned Reads │ cghub         │
├──────────┼────────┼────────┼───────────────┼───────────────┼───────────────┤
│ FI99990  │  435.7 │ MB     │ BAM           │ Aligned Reads │ cghub         │
├──────────┼────────┼────────┼───────────────┼───────────────┼───────────────┤
│ FI250134 │ 197.44 │ KB     │ VCF           │ StGV          │ collaboratory │
╘══════════╧════════╧════════╧═══════════════╧═══════════════╧═══════════════╛
╒══════════════════════╤════════╤════════╤══════════════╤═══════════════╕
│                      │   Size │ Unit   │   File Count │   Donor_Count │
╞══════════════════════╪════════╪════════╪══════════════╪═══════════════╡
│ collaboratory        │ 197.44 │ KB     │            1 │             1 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ collaboratory: StGV  │ 197.44 │ KB     │            1 │             1 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ cghub                │   3.94 │ GB     │            2 │             2 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ cghub: Aligned Reads │   3.94 │ GB     │            2 │             2 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ Total                │   3.94 │ GB     │            3 │             3 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ Total: Aligned Reads │   3.94 │ GB     │            2 │             2 │
├──────────────────────┼────────┼────────┼──────────────┼───────────────┤
│ Total: StGV          │ 197.44 │ KB     │            1 │             1 │
╘══════════════════════╧════════╧════════╧══════════════╧═══════════════╛
Valid access to the Collaboratory.
Valid access to the cghub files.
```

The only other subcommand is to check the version of all clients used by ICGC Get.  This command 
will only work if toolpaths are specified in the config file provided
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
# Repository specific configuration
Most configuration options can either be overwritten through the command line or environmental variables.
Environmental variables are in all caps, have underscores as separators, and are prefixed by ICGCGET_.
Command line options have dashes as separators and are prefixed by two dashes.  Config file options 
have periods as separators.  The only exception to this rule is the icgc api path.  It can only
be modified through the config file.

The config file can be specified either by passing an absolute path to the config to the 
command line with `--config`, or by making an environmental variable `ICGCGET_CONFIG` that contains 
the absolute path.  If neither of these options are chosen, the tool will look for  `.icget/config.yaml`
in your home directory.

All clients require an absolute path to your local client installation under repo.path in the config file or 
ICGCGET_REPO_PATH as an environmental variable.  All clients support the ability to configure the number of 
data streams to use when downloading under repo.transport.parallel or REPO_TRANSPORT_PARALLEL
Most clients can be made to download using the UDT protocol by using the repo.udt config option.
### Collaboratory and aws-virigina:

Provide an UUID for your icgc access token, and the transport file from protocol. (remote or 
    
### EGA
Ega access should be provided as an absolute path to a text file containing your ega username on the first line and your ega password on the second line.
It should be noted that there have been reliability issues experienced should the transport parallel of the ega client increase beyond 1.

### GDC
GDC access should be provided as the UUID of your gdc access token

### CGHub
CGHub access should be provided as an absolute path to a cghub.key file.

### PDC
PDC access should be provided as an absolute path to a text file containing your aws key on the first line and your aws secret key on the second line.
It is also necessary to specify your aws region under aws.region See http://docs.aws.amazon.com/general/latest/gr/rande.html to determine your region.

# Unit Tests

Unit tests have been provided in the tests directory of the repository.  They require a configuration file with valid
EGA and cghub credentials to be saved in the root of the repository.

To run unit tests, execute the following:

```shell
python setup.py test
```
