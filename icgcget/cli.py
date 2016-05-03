#
# Copyright (c) 2016 The Ontario Institute for Cancer Research. All rights reserved.
#
# This program and the accompanying materials are made available under the terms of the GNU Public License v3.0.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <http://www.gnu.org/licenses/>.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT
# SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import logging
import os

import click
import yaml

from clients.ega import ega_client
from clients.gdc import gdc_client
from clients.gnos import gt_client
from clients.icgc import icgc_api
from clients.icgc import icgc_client
from utils import flatten_dict, normalize_keys, match_repositories

REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']  # Updated for codes used by api

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')


def config_parse(filename):
    config = {}
    try:
        config_text = open(filename, 'r')
    except IOError:

        print("Config file {} not found".format(filename))
        return config

    try:
        config_temp = yaml.safe_load(config_text)
        config_download = flatten_dict(normalize_keys(config_temp))
        config = {'download': config_download, 'logfile': config_temp['logfile']}
    except yaml.YAMLError:

        print("Could not read config file {}".format(filename))
        return {}

    return config


def logger_setup(logfile):
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    if logfile is not None:
        fh = logging.FileHandler(logfile)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(sh)
    return logger


def check_code(code):
    if code != 0:
        logger = logging.getLogger('__log__')
        logger.error("client exited with a nonzero error code {}.".format(code))
        click.ClickException("Please check client output for error messages")


def check_access(access, name):
    if access is None:
        logger = logging.getLogger('__log__')
        logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter

@click.group()
@click.option('--config', default=DEFAULT_CONFIG_FILE)
@click.option('--logfile', default=None)
@click.pass_context
def cli(ctx, config, logfile):
    config_file = config_parse(config)
    if config != DEFAULT_CONFIG_FILE and not config_file:
        raise click.BadParameter(message="Invalid config file")
    ctx.default_map = config_file

    if logfile is not None:
        logger_setup(logfile)
    elif 'logfile' in config_file:
        logger_setup(config_file['logfile'])
    else:
        logger_setup(None)


@cli.command()
@click.argument('fileids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True, required=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=False))
@click.option('--portal-api')
@click.option('--portal-url')
@click.option('--cghub-access')
@click.option('--cghub-path')
@click.option('--cghub-transport-parallel')
@click.option('--ega-access')
@click.option('--ega-password')
@click.option('--ega-path')
@click.option('--ega-transport-parallel')
@click.option('--ega-udt')
@click.option('--ega-username')
@click.option('--gdc-access')
@click.option('--gdc-path')
@click.option('--gdc-transport-parallel')
@click.option('--gdc-udt')
@click.option('--icgc-access')
@click.option('--icgc-path')
@click.option('--icgc-transport-file-from')
@click.option('--icgc-transport-parallel')
def download(repos, fileids, manifest, output, portal_api, portal_url,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_access, ega_password, ega_path, ega_transport_parallel, ega_udt, ega_username,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel):
    logger = logging.getLogger('__log__')
    api_url = portal_url+portal_api
    object_ids = {}
    if 'ega' in repos:
        if ega_username is None or ega_password is None:
            check_access(ega_access, 'ega')
    if 'collaboratory' in repos or 'aws-virginia' in repos:
        check_access(icgc_access, 'icgc')
    if 'cghub' in repos:
        check_access(cghub_access, 'cghub')
    if 'gdc' in repos:
        check_access(gdc_access, 'gdc')

    for repository in repos:
        object_ids[repository] = []
    entities = []
    if manifest:
        entities = icgc_api.read_entity_set(fileids, api_url)
    else:
        for fileid in fileids:
            entity = icgc_api.get_metadata(fileid, api_url)
            if not entity:
                raise click.ClickException("File not found")
            entities.append(entity)
    for entity in entities:
        repository, copy = match_repositories(repos, entity)
        if repository is None:
            logger.error("File {} not found on repositories {}".format(entity["id"], repos))
            raise click.BadParameter("File {} not found on repositories {}".format(entity["id"], repos))
        elif repository == 'collaboratory' or repository == 'aws-virginia':
            object_ids[repository].append(entity["objectId"])
        else:
            object_ids[repository].append(entity["dataBundle"]["dataBundleId"])

    if 'aws-virginia' in repos:
        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            if len(object_ids['aws-virginia']) > 1:  # Todo-find a workaround for this: dynamic manifest generation?
                logger.error("The icgc repository does not support input of multiple file id values.")
                raise click.BadParameter
            code = icgc_client.icgc_call(object_ids['aws-virginia'], icgc_access, icgc_path, icgc_transport_file_from,
                                         icgc_transport_parallel, output, 'aws')
            check_code(code)

    if 'ega' in repos:
        if object_ids['ega']:
            if len(object_ids['ega']) > 1:  # Todo-find a workaround for this rather than throw errors
                logger.error("The ega repository does not support input of multiple file id values.")
                raise click.BadParameter
            else:
                if ega_transport_parallel != '1':
                    logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                   "downloads.  This option is not recommended.")
                code = ega_client.ega_call(object_ids['ega'], ega_username, ega_password, ega_path,
                                           ega_transport_parallel, ega_udt, output)
                check_code(code)

    if 'cghub' in repos:
        if object_ids['cghub']:
            code = gt_client.genetorrent_call(object_ids['cghub'], cghub_access, cghub_path,
                                              cghub_transport_parallel, output)
            check_code(code)

    if 'collaboratory' in repos:
        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            if len(object_ids['collaboratory']) > 1:  # Todo-find a workaround for this: ask for extra functionality?
                logger.error("The icgc repository does not support input of multiple file id values.")
                raise click.BadParameter
            else:
                code = icgc_client.icgc_call(object_ids['collaboratory'], icgc_access, icgc_path,
                                             icgc_transport_file_from, icgc_transport_parallel, output, 'collab')
                check_code(code)

    if 'gdc' in repos:
        if object_ids['gdc']:
            code = gdc_client.gdc_call(object_ids['gdc'], gdc_access, gdc_path, output, gdc_udt, gdc_transport_parallel)
            check_code(code)


def main():
    cli(auto_envvar_prefix='ICGCGET')

if __name__ == "__main__":
    main()
