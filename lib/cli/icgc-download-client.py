import argparse
import logging
import yaml

from clients.ega import ega_script
from clients.gdc import gdc_script
from clients.gnos import genetorrent
from clients.icgc import icgc_script


def config_parse(filename):

    try:
        config_text = open(filename, 'r')
    except IOError:
        print "Config file not found: Aborting"
        return
    try:
        config_temp = yaml.load(config_text)
    except yaml.YAMLError:
        print "Could not read config file: Aborting"
        return
    return config_temp


def logger_setup(logfile):

    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    fh = logging.FileHandler(logfile)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    return logger


repos = ['ega', 'collab', 'cghub', 'aws', 'gdc']

parser = argparse.ArgumentParser()
parser.add_argument("--config", nargs='?', default="/icgc/mnt/configuration/config.yaml",
                    help="File used to set download preferences and authentication criteria")
parser.add_argument('repo', choices=repos, help='Specify which repository to download from, all lowercase letters')
parser.add_argument('-f', '--file_id', help='Lowercase identifier of file or path to manifest file')
parser.add_argument('-m', '--manifest', help='Flag used when the downloading from a manifest file')
parser.add_argument('--output_dir', nargs='?', default='/icgc/mnt/downloads', help='Directory to save downloaded files')
args = parser.parse_args()

config = config_parse(args.config)
logger_setup(config['logfile'])
logger = logging.getLogger('__log__')

if args.repo == 'ega':
    if args.file_id is not None:  # ega does not support manifest files
        ega_script.ega_call(args.file_id, config['access.ega'], config['tool.ega'], config['udt'], args.output_dir)
    if args.manifest is not None:
        logger.warning("The ega repository does not support downloading from manifest files.  Use the -f tag instead")
elif args.repo == 'collab' or args.repo == 'aws':
    if args.manifest is not None:
        icgc_script.icgc_manifest_call(args.manifest, config['access.icgc'], config['tool.icgc'], args.output_dir)
    if args.file_id is not None:  # This code exists to let users use both file id's and manifests in one command
        icgc_script.icgc_call(args.file_id, config['access.icgc'], config['tool.icgc'], args.output_dir)
elif args.repo == 'cghub':
    if args.manifest is not None:
        genetorrent.genetorrent_call(args.manifest, config['access.cghub'], config['tool.cghub'], args.output_dir)
    if args.file_id is not None:
        genetorrent.genetorrent_call(args.file_id, config['access.cghub'], config['tool.cghub'], args.output_dir)
elif args.repo == 'gdc':
    if args.manifest is not None:
        gdc_script.gdc_manifest_call(args.manifest, config['access.gdc'], config['tool.gdc'], args.output_dir,
                                     config['udt'])
    if args.file_id is not None:
        gdc_script.gdc_call(args.file_id, config['access.gdc'], config['tool.gdc'], args.output_dir, config['udt'])
else:
    logger.error("Please provide either a file id value or a manifest file to download")
