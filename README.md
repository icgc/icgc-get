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

To install ICGC get on your local machine , first download the ICGC get package.
Then navigate to the `icgc-get` directory and run the command:

```shell
python setup.py install
```

Once the installation is complete, ICGC get can be invoked with the command `icgc-get`

ICGC get is also available as a docker container.  Running ICGC get through a 
docker container will prevent issues from arising related to conflicting 
software requirements for the data download clients. The docker container will also
automatically install all supported data clients.

First, install docker from https://docs.docker.com/mac/. Then pull the docker image using the command

```shell
docker pull icgc/icgc-get
```

To make working with the container easier, it is recommend to add a bash alias to enable invocation of ICGC get with the command
`icgc-get`.

```shell
alias icgc-get="docker run -it --rm -v $MOUNT_DIR:/icgc/mnt icgc/icgc-get --config /icgc/mnt/config.yaml"
```


replacing `$MOUNT_DIR` with the path to your mounted directory. This directory will be populated by the script with
process logs and downloaded files. You will also need to save a configuration file in this directory if you wish
to pass a customized config file to the container.


## Configuration
ICGC get is packaged with a default configuration file `config.yaml`, that contains a list of all
configurable options and the defaults for using these options in a docker container.
In addition to editing the config file most configuration options can either be overwritten 
through the command line or environmental variables. Environmental variables are in all caps, 
have underscores as separators, and are prefixed by ICGCGET_. Command line options have dashes 
as separators and are prefixed by two dashes.  Config file options a colon, followed by a newline and two spaces as separators.  The 
only exception to this rule is the ICGC api path: it cannot be set via the command line.

To specify which config file to use either pass an absolute path to the config file to the 
command line with `--config`, or declare an environmental variable `ICGCGET_CONFIG` that contains 
the absolute path.  If neither of these options are chosen, the tool will look for  `.icgc-get/config.yaml`
in your home directory.

It is necessary to specify the directory for downloaded files to be saved to under `output` if you are running 
ICGC get locally.  Please make sure that this directory offers read-write-execute permissions to all users.

It is also recommended to specify a common list of repositories in your preferred order of precedence.  When downloading
a file, the tool will first try to find the file on the first specified repository, then the second, ect cetra.
Please use the following format to define your repositories in the configuration file.

```yaml
repos:
 - collaboratory
 - cghub
 - pdc
```

Valid repositories are:

| Code             | Repository                     |
| --------         | -------------------------------|
| `aws-virginia`   | Amazon Web Services            |
| `collaboratory`  | Collaboratory                  |
| `ega`            | European Genome Association    |
| `gdc`            | Genomic Data Commons           |
| `cghub`          | Cancer Genomic Hub             |
| `pdc`            | Bionimbus Protected Data Cloud |

All clients require an absolute path to your local client installation under repo.path in the config file or 
`ICGCGET_REPO_PATH` as an environmental variable.  All clients support the ability to configure the number of 
data streams to use when downloading under `repo.transport.parallel` or `REPO_TRANSPORT_PARALLEL`
Most clients can be made to download using the UDT protocol by using the `repo.udt` config option.

## Access

### Collaboratory and AWS

These repositories are both accessed through the [`icgc-storage-client`](https://hub.docker.com/r/icgc/icgc-storage-client/), and share their 
configuration parameters under the icgc namespace.  For both of these repositories 
provide an UUID for your icgc access token as the `icgc.access` parameter. 
You may also specify the transport file from protocol, under `icgc.file.from`. 
Further documentation can be found at http://docs.icgc.org/cloud/guide/.
To apply for access to Collaboratory and AWS see https://icgc.org/daco.

### EGA
[EGA](https://ega-archive.org/) access should be provided as an absolute path to a text file containing your ega username on the first line and your ega password on the second line.
It should be noted that there have been reliability issues experienced should the transport parallel of the ega client increase beyond 1.
Further information can be found at https://www.ebi.ac.uk/ega/about/access

### GDC
[GDC](https://gdc.nci.nih.gov) access should be provided as the UUID of your gdc access token.  Further information
about access can be found at https://gdc-docs.nci.nih.gov/Data_Transfer_Tool/Users_Guide/Preparing_for_Data_Download_and_Upload/

### CGHub
[CGHub](https://cghub.ucsc.edu/) access should be provided as an absolute path to a cghub.key file.
Information about how to acquire a cghub key file can be found 
https://cghub.ucsc.edu/access/get_access.html.

### PDC

[PDC](https://bionimbus-pdc.opensciencedatacloud.org) access should be provided as an absolute path to a text file containing your aws key on the first line and your aws secret key on the second line.
Support for the PDC can be reached at https://bionimbus-pdc.opensciencedatacloud.org
It is also necessary to specify your aws region under `aws.region` See http://docs.aws.amazon.com/general/latest/gr/rande.html to determine your region.

## Commands

### `download` command

The syntax for performing a download using ICGC get is
```shell
icgc-get --config [CONFIG] download [REPO] [FILEIDS] [OPTIONS]
```

The first required argument is the repository or repositories that are being targeted for download, provided they have not been
specified in the config file.
Prepend each repository with the `-r`, for example `-r aws-virginia -r ega`.  The order that the repositories
are listed is important: files will be downloaded from the first specified repository if possible, and subsequent repositories
only if the file was not found on any previous repository.

The second required argument is the ICGC File ids or manifest id corresponding to the file or files you wish to download. 
There is no special syntax for this argument. If this is for a manifest id append the tag `-m` or `--manifest`. These ids may be retrieved from the 
ICGC data portal: https://dcc.icgc.org. 

The download command comes with an automatic prompt that warns the user if the projected download size approaches the 
total available space in the download directory.  It is possible to suppress this warning using the `-y` flag.

Then execute the command as normal:

```shell
icgc-get download FI378424 -r  collaboratory
```

### `status` command

For very large downloads, it may be useful to check the progress of the download process.
The status command can be run in another terminal while ICGC get is downloading files to 
provide an update on their progress.  The only argument it takes is `--output`, which must point to
the same output directory as the download in progress points to.

```shell
icgc-get status
```

Sample output
```shell

```

### `report` command

Another useful subcommand is `status`.  This takes the same primary inputs as `download`,
but instead of downloading the specified files, it will provide a list of all files that are
about to be downloaded, including their size, data type, name and the repository they are hosted on. 
By default the command outputs a table, but by using the `-t` flag it can be converted into tsv format.

```shell
icgc-get report FI99996 FI99990 FI250134 -r collaboratory -r cghub
```

Sample output:

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
```

### `summary` command

The `summary` command is a companion to `report` It will also provide a summary of the download by 
repository and data type, showing how many files and the total size of the files for each category.  
It is primarily used if the number of files is too large for a single `report` to be easily human readable.
Like `report`, its output can be converted to tsv format with the flag `t`.

```shell
icgc-get summary FI99996 FI99990 FI250134 -r collaboratory -r cghub
```

Sample output:

```
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
```

### `check` command

The `check` command will test the provided credentials for each repository specified.
Due to the security protocols of each client, there are two ways in which this access check can occur.
For PDC, GDC, and CGHub, ICGC get is only capable of determining if you have access to the specific 
files targeted for download, not the state of your permissions for the repository as a whole.  
When performing an access check for these repositories, you must provide a manifest id or 
list of files using the same formatting as the download command.  Inquests about permissions on these 
repositories should be directed to their respective support department.

For the AWS, collaboratory, and ega repositories, the access check will determine if you have access
to the entire repository or not.  These checks will occur even if file prioritization leads to no files
being downloaded from any of these repositories.    

To do a status check on the same files:

```shell
icgc-get check FI99996 FI99990 FI250134 -r collaboratory -r cghub
```

Sample output:

```
Valid access to the Collaboratory.
Valid access to the cghub files.
```

### `version` Command

The only other subcommand is to display the version of all clients used by ICGC Get. This command 
will only work if tool paths are specified in the config file provided.

```shell
icgc-get version
```

Sample output:

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
