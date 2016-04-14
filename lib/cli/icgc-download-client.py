import argparse
import logging

import yaml

from lib.clients.ega import ega_script
from lib.clients.gdc import gdc_script
from lib.clients.gnos import genetorrent
from lib.clients.icgc import icgc_script

parser = argparse.ArgumentParser()
parser.add_argument("--config", nargs='?', default="/icgc/mnt/configuration/config.yaml",
                    help="File used to set download preferences and authentication criteria")
parser.add_argument('repo', choices=['ega', 'collab', 'cghub', 'aws', 'gdc'],
                    help='specify which repository to download from, all lowercase letters')
parser.add_argument('--file_id', help='identifier of file or files')
parser.add_argument('--manifest', help='Path to manifest file of IDs for icgc only')
parser.add_argument('--output_dir', nargs='?', default="/icgc//mnt/downloads",
                    help="specify directory to store downloaded files")
args = parser.parse_args()
configtext = open(args.config, 'r')

config = yaml.load(configtext)

logging.basicConfig(filename=config['logfile'], level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

if args.repo == 'ega':
    ega_script.ega_call(args.file_id, config['access.ega'], config['udt'])
elif args.repo == 'collab' | args.repo == 'aws':
    if args.file_id != '':
        icgc_script.icgc_call(args.file_id, config['access.icgc'], args.repo, config['download.directory'])
    elif args.manifest != '':
        icgc_script.icgc_manifest_call(args.manifest, config['access.icgc'], args.repo, config['download.directory'])
elif args.repo == 'cghub':
    genetorrent.genetorrent_call(args.file_id, config['access.cghub'], config['download.directory'])
elif args.repo == 'gdc':
    if args.file_id != '':
        gdc_script.gdc_call(args.file_id, config['access.gdc'], config['download.directory'], config['udt'])
    elif args.manifest != '':
        gdc_script.gdc_manifest_call(args.manifest, config['access.gdc'], config['download.directory'], config['udt'])




