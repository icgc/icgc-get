# ICGC Get
Universal download client for ICGC data residing in various environments. 

# Installation

To install ICGC get on your local machine , first download the ICGC get package.
Then navigate to the `icgc-get` directory and run the command:

```shell
python setup.py install
```

ICGC get is also available as a docker container.  Running ICGC get through a 
docker container will prevent issues from arising related to conflicting 
software requirements for the data download clients. The docker container will also
automatically install all supported data clients.

First, install docker from https://docs.docker.com/mac/. Then pull the docker image using the command

`docker pull icgc/icgc-get`

To save some typing, you can add a bash alias to make working with the container easier:

```shell
alias icgc-get="docker run -it --rm -v {MNT_DIR}:/icgc/mnt icgc/icgc-get --config /icgc/mnt/config.yaml"
```

replacing `{PATH}` with the path to your mounted directory. This directory will be populated by the script with
process logs and downloaded files. This will enable the invocation of the python script with the command `icgc-get`. 


# Configuration
ICGC get is packaged with a default congfiguration file `config.yaml`, that contains a list of all
configurable options and the defaults for using these options in a docker container.
In addition to editing the config file most configuration options can either be overwritten 
through the command line or environmental variables. Environmental variables are in all caps, 
have underscores as separators, and are prefixed by ICGCGET_. Command line options have dashes 
as separators and are prefixed by two dashes.  Config file options have periods as separators.  
The only exception to this rule is the icgc api path.  It can only be modified through the config file.

To specify which config file to use either pass an absolute path to the config file to the 
command line with `--config`, or declare an environmental variable `ICGCGET_CONFIG` that contains 
the absolute path.  If neither of these options are chosen, the tool will look for  `.icget/config.yaml`
in your home directory.

It is necessary to specify the directory for downloaded files to be saved to if you are running 
ICGC-get locally.  Please make sure that this directory offers read-write-execute permissions to all users.

All clients require an absolute path to your local client installation under repo.path in the config file or 
`ICGCGET_REPO_PATH` as an environmental variable.  All clients support the ability to configure the number of 
data streams to use when downloading under repo.transport.parallel or `REPO_TRANSPORT_PARALLEL`
Most clients can be made to download using the UDT protocol by using the `repo.udt` config option.

# Access

### Collaboratory and AWS:

These repositories are both accessed through the icgc storage client, and share their 
configuration parameters under the icgc namespace.  For both of these repositories 
provide an UUID for your icgc access token as the `icgc.access` parameter. 
You may also specify the transport file from protocol, under `icgc.file.from`. 
Further documentation can be found at http://docs.icgc.org/cloud/guide/.
To apply for access to Collaboratory and AWS see https://icgc.org/daco.

### EGA
Ega access should be provided as an absolute path to a text file containing your ega username on the first line and your ega password on the second line.
It should be noted that there have been reliability issues experienced should the transport parallel of the ega client increase beyond 1.
Further information can be found at https://www.ebi.ac.uk/ega/about/access

### GDC
GDC access should be provided as the UUID of your gdc access token.  Further information
about access can be found a https://gdc-docs.nci.nih.gov/Data_Transfer_Tool/Users_Guide/Preparing_for_Data_Download_and_Upload/

### CGHub
CGHub access should be provided as an absolute path to a cghub.key file.
Information about how to acquire a cghub key file can be found 
https://cghub.ucsc.edu/access/get_access.html

### PDC
PDC access should be provided as an absolute path to a text file containing your aws key on the first line and your aws secret key on the second line.
Support for the PDC can be reached at https://bionimbus-pdc.opensciencedatacloud.org
It is also necessary to specify your aws region under aws.region See http://docs.aws.amazon.com/general/latest/gr/rande.html to determine your region.

#Commands

### Download

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

Prepend each repository with the `-r`, for example `-r aws-virginia -r ega`.  The order that the repositories
are listed is important: files will be downloaded from the first specified repository if possible, and subsequent repositories
only if the file was not found on any previous repository.

Second you must specify an ICGC File ids or manifest id corresponding to the file or files you wish to download. 
If this is for a manifest id append the tags `-m` or `--manifest`. These Ids may be retrieved from the 
ICGC data portal https://dcc.icgc.org. 

The download command comes with an automatic prompt that warns the user if the projected download size approaches the 
total available space in the download directory.  It is possible to supress this warning using the `-y` flag.

Then execute the command as normal:

```shell
icgc-get download FI378424 -r  collaboratory
```

### Status
Another useful subcommand is `status`.  This takes the same primary inputs as `download`,
but instead of downloading the specified files, it will provide a list of all files that are
about to be downloaded, including their size, data type, and the repository they are hosted on.
It will also provide a summary of the download by repository and data type, showing how many files
and the total size of the files for each category.  In case of very large downloads, the individual
file summary may be too large to be practical, and it can be suppressed with the flag `-nf`. 

In addition, the status command will test the provided credentials for each repository specified.
Due to the security protocols of each client, there are two ways in which this access check can occur.
For the AWS, collaboratory, and ega repositories, the access check will determine if you have access
to the entire repository or not.  These checks will occur even if file prioritization leads to no files
being downloaded from any of these repositories.  For PDC, GDC, and CGHub, ICGC get is only capable of 
determining if you have access to the specific files targeted for download or not.  

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

### Version
The only other subcommand is to check the version of all clients used by ICGC Get.  This command 
will only work if tool paths are specified in the config file provided.
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

# Unit Tests

Unit tests have been provided in the tests directory of the repository.  They require a configuration file with valid
EGA and cghub credentials to be saved in the root of the repository.

To run unit tests, execute the following:

```shell
python setup.py test
```
