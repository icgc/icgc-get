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
from clients.icgc import icgc_client
from clients.icgc import icgc_api
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
@click.option('--repo', '-r', type=click.Choice(REPOS), multiple=True, required=True)
@click.option('--manifest', '-m', default=False)
@click.option('--output', type=click.Path(exists=False))
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
@click.option('--icgc-transport-memory')
@click.option('--icgc-transport-parallel')
def download(repo, fileids, manifest, output,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_access, ega_password, ega_path, ega_transport_parallel, ega_udt, ega_username,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_memory, icgc_transport_parallel):
    logger = logging.getLogger('__log__')

    object_ids = {}
    if 'ega' in repo:
        if ega_username is None or ega_password is None:
            if ega_access is None:  # Do we want to raise exceptions on these, or just run them all?
                logger.error("No credentials provided for the ega repository.")
                raise click.BadParameter
    if 'collaboratory' in repo or 'aws-virginia' in repo:
        if icgc_access is None:
            logger.error("No credentials provided for the icgc repository")
            raise click.BadParameter
    if 'cghub' in repo:
        if cghub_access is None:
            logger.error("No credentials provided for the cghub repository.")
            raise click.BadParameter
    if 'gdc' in repo:
        if gdc_access is None:
            logger.error("No credentials provided for the gdc repository.")
            raise click.BadParameter

    for repository in repo:
        object_ids[repository] = []

    for fileid in fileids:
        info = icgc_api.check_file(fileid)
        if type(info) is int:
            raise click.ClickException("File not found")
        repository, copy = match_repositories(repo, info)
        if repository is None:
            logger.error("File {} specified not found on repositories {}".format(info["id"], repo))
        object_ids[repository].append(copy["indexFile"]["objectId"])

    if 'aws-virginia' in repo:
        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            if len(object_ids['aws-virginia']) > 1:  # Todo-find a workaround for this: dynamic manifest generation?
                logger.error("The icgc repository does not support input of multiple file id values.")
                raise click.BadParameter
            code = icgc_client.icgc_call(object_ids['aws-virginia'], icgc_access, icgc_path, icgc_transport_file_from,
                                         icgc_transport_parallel, output, 'aws')

    if 'ega' in repo:
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
                if code != 0:
                    logger.error("client exited with a nonzero error code {}.".format(code))
                    click.ClickException("Please check client output for error messages")

    if 'cghub' in repo:
        if object_ids['cghub']:
            code = gt_client.genetorrent_call(object_ids['cghub'], cghub_access, cghub_path,
                                              cghub_transport_parallel, output)
            if code != 0:
                logger.error("client exited with a nonzero error code {}.".format(code))
                click.ClickException("Please check client output for error messages")

    if 'collaboratory' in repo:
        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            if len(object_ids['collaboratory']) > 1:  # Todo-find a workaround for this: ask for extra functionality?
                logger.error("The icgc repository does not support input of multiple file id values.")
                raise click.BadParameter
            else:
                code = icgc_client.icgc_call(object_ids['collaboratory'], icgc_access, icgc_path,
                                             icgc_transport_file_from, icgc_transport_parallel, output, 'collab')
                if code != 0:
                    logger.error("client exited with a nonzero error code {}.".format(code))
                    click.ClickException("Please check client output for error messages")

    if 'gdc' in repo:
        if object_ids['gdc']:
            code = gdc_client.gdc_call(object_ids['gdc'], gdc_access, gdc_path, output, gdc_udt, gdc_transport_parallel)
            if code != 0:
                logger.error("client exited with a nonzero error code {}.".format(code))
                click.ClickException("Please check client output for error messages")

if __name__ == "__main__":
    cli(auto_envvar_prefix='ICGCGET')
