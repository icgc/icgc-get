import argparse
import logging

import yaml
import subprocess

from clients.ega import ega_script
from clients.gdc import gdc_script
from clients.gnos import genetorrent
from clients.icgc import icgc_script


def config_parse(filename):
    try:
        configtext = open(filename, 'r')
    except IOError:
        print "Config file not found"
    try:
        config_temp = yaml.load(configtext)
    except yaml.YAMLError:
        print "Could not read config file"
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
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger



parser = argparse.ArgumentParser()
parser.add_argument("--config", nargs='?', default="/icgc/mnt/configuration/config.yaml",
                    help="File used to set download preferences and authentication criteria")
parser.add_argument('repo', choices=['ega', 'collab', 'cghub', 'aws', 'gdc'],
                    help='specify which repository to download from, all lowercase letters')
parser.add_argument('file_id', help='Lowercase identifier of file or path to manifest file')
parser.add_argument('-m', '--manifest', action='store_true', help='Flag used when the downloading from a manifest file')

args = parser.parse_args()
config = config_parse(args.config)
logger_setup(config['logfile'])
logger = logging.getLogger('__log__')

if args.repo == 'ega':
    ega_script.ega_call(args.file_id, config['access.ega'], config['tool.ega'], config['udt'],
                        config['download.directory'])
elif args.repo == 'collab' or args.repo == 'aws':
    if args.manifest:
        icgc_script.icgc_manifest_call(args.file_id, config['access.icgc'],
                                       config['tool.icgc'], config['download.directory'])
    else:
        icgc_script.icgc_call(args.file_id, config['access.icgc'], config['tool.icgc'], config['download.directory'])
elif args.repo == 'cghub':
    genetorrent.genetorrent_call(args.file_id, config['access.cghub'], config['tool.cghub'],
                                 config['download.directory'])
elif args.repo == 'gdc':
    if args.manifest:
        gdc_script.gdc_manifest_call(args.file_id, config['access.gdc'], config['tool.gdc'],
                                     config['download.directory'], config['udt'])
    else:
        gdc_script.gdc_call(args.file_id, config['access.gdc'], config['tool.gdc'],
                            config['download.directory'], config['udt'])
else:
    logger.info('No valid repository specified.  Valid repositories are: aws, collab, cghub, gdc,and ega')