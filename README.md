# icgc-download-client
Universal download client for ICGC data residing in various environments. 

Using the python script:

The required arguments for the python script are the repository that is being targeted for download.
Valid repositories are aws (Amazon Web Services ), collab (Collabratory), ega (European Genome Association)
gdc(Genomic data commons) and cghub (Cancer genomic hub)

Second required argument is the object id, a unique, repository specific identifier for the object to download.

If not running the tool in a docker container, a user must also specify the --output_dir where files are to be saved
and the --config, the location of the configuration file.  Absolute paths are required for both arguments.

*WORK IN PROGRESS*
