# icgc-download-client
Universal download client for ICGC data residing in various environments. 

## Using the python script:

The required arguments for the python script are the repository that is being targeted for download.
Valid repositories are aws _(Amazon Web Services)_, collab _(Collabratory)_, ega _(European Genome Association)_
gdc _(Genomic data commons)_ and cghub _(Cancer genomic hub)_

Second you must specify either a file id using the tag -f or --file_id, a manifest file using the tags -m or -manifest
or both.  This will specify the file or files to be downloaded.  **The EGA repository does not currently support
downloads using a manifest file.**  It is possible to specify multiple file ID's using th -f flag when downloading from the
gdc or cghub repositories.  **The EGA and ICGC repositories do not support this functionality**

If not running the tool in a docker container, a user must also specify the --output_dir where files are to be saved
and the --config, the location of the configuration file.  **Absolute paths are required for both arguments.**


