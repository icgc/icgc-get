#!/usr/bin/python
# -*- coding: utf-8 -*-
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

import json
import logging
import os
import sys

import click

from icgcget.commands.access_checks import AccessCheckDispatcher
from icgcget.commands.configure import ConfigureDispatcher
from icgcget.commands.download import DownloadDispatcher
from icgcget.commands.reports import StatusScreenDispatcher
from icgcget.commands.utils import compare_ids, config_parse, validate_ids, load_json, filter_repos
from icgcget.commands.versions import versions_command
from icgcget.params import RepoParam, LogfileParam
from icgcget.version import __version__, __container_version__

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')
API_URL = "https://staging.dcc.icgc.org/api/v1/"
DOCKER_PATHS = {'icgc_path': '/icgc/icgc-storage-client/bin/icgc-storage-client',
                'ega_path': '/icgc/ega-download-demo/EgaDemoClient.jar',
                'cghub_path': '/icgc/genetorrent/bin/gtdownload', 'pdc_path': '/usr/local/bin/aws',
                'gdc_path': '/icgc/gdc-data-transfer-tool/gdc-client'}


def logger_setup(logfile, verbose):
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)

    if logfile:
        try:
            open(logfile, 'a')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler = logging.FileHandler(logfile, mode='a')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except IOError as ex:
            if not ex.errno == 2:
                print "Unable to write to logfile '{}'".format(logfile)

    stream_handler = logging.StreamHandler()
    if verbose:
        stream_handler.setLevel(logging.DEBUG)
    else:
        stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)
    return logger


def get_container_tag(context_map):
    if os.getenv("ICGCGET_CONTAINER_TAG"):
        tag = os.getenv("ICGCGET_CONTAINER_TAG")
    elif context_map and "container_tag" in context_map.default_map:
        tag = context_map.default_map["container_tag"]
    else:
        tag = __container_version__
    return tag


@click.group()
@click.option('--config', default=DEFAULT_CONFIG_FILE, envvar='ICGCGET_CONFIG')
@click.option('--docker', '-d', type=click.BOOL, default=None, envvar='ICGCGET_DOCKER')
@click.option('--logfile', type=LogfileParam(), default=None, envvar='ICGCGET_LOGFILE')
@click.option('--verbose', '-v', is_flag=True, default=False, help="Do not verify ssl certificates")
@click.pass_context
def cli(ctx, config, docker, logfile, verbose):
    if ctx.invoked_subcommand != 'configure':
        config_file = config_parse(config, DEFAULT_CONFIG_FILE, docker, DOCKER_PATHS)
        if config != DEFAULT_CONFIG_FILE and not config_file:
            raise click.Abort()
        if docker is not None:
            ctx.obj = docker
        elif 'docker' in config_file:
            ctx.obj = config_file['docker']
        else:
            ctx.obj = True
        if logfile is not None:
            logger = logger_setup(logfile, verbose)
        elif 'logfile' in config_file:
            logger = logger_setup(config_file['logfile'], verbose)
        else:
            logger = logger_setup(None, verbose)
        ctx.default_map = config_file
        logger.debug(__version__ + ' ' + ctx.invoked_subcommand)


@cli.command()
@click.argument('IDS', nargs=-1, required=True)
@click.option('--repos', '-r', multiple=True, type=RepoParam())
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              required=True, envvar='ICGCGET_OUTPUT')
@click.option('--cghub-key', type=click.STRING, envvar='ICGCGET_CGHUB_KEY')
@click.option('--cghub-path', envvar='ICGCGET_CGHUB_PATH')
@click.option('--cghub-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_CGHUB_TRANSPORT_PARALLEL')
@click.option('--ega-username', type=click.STRING, envvar='ICGCGET_EGA_USERNAME')
@click.option('--ega-password', type=click.STRING, envvar='ICGCGET_EGA_PASSWORD')
@click.option('--ega-path', envvar='ICGCGET_EGA_PATH')
@click.option('--ega-transport-parallel', type=click.STRING, default='1', envvar='ICGCGET_EGA_TRANSPORT_PARALLEL')
@click.option('--ega-udt', default=False, envvar='ICGCGET_EGA_UDT')
@click.option('--gdc-token', type=click.STRING, envvar='ICGCGET_GDC_TOKEN')
@click.option('--gdc-path', envvar='ICGCGET_GDC_PATH')
@click.option('--gdc-transport-parallel', type=click.STRING, default='8')
@click.option('--gdc-udt', default=False, envvar='ICGCGET_GDC_UDT')
@click.option('--icgc-token', type=click.STRING, envvar='ICGCGET_ICGC_TOKEN')
@click.option('--icgc-path', envvar='ICGCGET_CGHUB_ACCESS')
@click.option('--icgc-transport-file-from', type=click.STRING, default='remote',
              envvar='ICGCGET_ICGC_TRANSPORT_FILE_FROM')
@click.option('--icgc-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_PDC_TRANSPORT_PARALLEL')
@click.option('--pdc-key', type=click.STRING, envvar='ICGCGET_PDC_KEY')
@click.option('--pdc-secret', type=click.STRING, envvar='ICGCGET_PDC_SECRET')
@click.option('--pdc-path', envvar='ICGCGET_PDC_PATH')
@click.option('--pdc-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_PDC_TRANSPORT_PARALLEL')
@click.option('--override', '-o', is_flag=True, default=True, help="Bypass all confirmation prompts")
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def download(ctx, ids, repos, manifest, output,
             cghub_key, cghub_path, cghub_transport_parallel,
             ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
             gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
             pdc_key, pdc_secret, pdc_path, pdc_transport_parallel, override, no_ssl_verify):
    logger = logging.getLogger('__log__')
    logger.debug(str(ctx.params))
    staging = output + '/.staging'
    filter_repos(repos)
    tag = get_container_tag(ctx)

    if not os.path.exists(staging):
        os.umask(0000)
        os.mkdir(staging, 0777)
    json_path = staging + '/state.json'

    old_download_session = load_json(json_path)
    dispatch = DownloadDispatcher(json_path, ctx.obj, ctx.default_map['logfile'], tag)
    if old_download_session and ids == old_download_session['command']:
        download_session = old_download_session
    else:
        validate_ids(ids, manifest)
        download_session = dispatch.download_manifest(repos, ids, manifest, output, API_URL, no_ssl_verify, unique=True)
    if old_download_session:
        download_session['file_data'] = compare_ids(download_session['file_data'], old_download_session['file_data'],
                                                    override)
    json.dump(download_session, open(json_path, 'w', 0777))
    dispatch.download(download_session, staging, output,
                      cghub_key, cghub_path, cghub_transport_parallel,
                      ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                      gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
                      icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                      pdc_key, pdc_secret, pdc_path, pdc_transport_parallel)
    os.remove(json_path)


@cli.command()
@click.argument('IDS', nargs=-1, required=False)
@click.option('--repos', '-r', multiple=True, type=RepoParam())
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              envvar='ICGCGET_OUTPUT')
@click.option('--table-format', '-f', type=click.Choice(['tsv', 'pretty', 'json']), default='pretty')
@click.option('--data-type', '-t', type=click.Choice(['file', 'summary']), default='file')
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def report(ctx, repos, ids, manifest, output, table_format, data_type, no_ssl_verify):
    logger = logging.getLogger('__log__')
    logger.debug(str(ctx.params))
    filter_repos(repos)
    tag = get_container_tag(ctx)

    json_path = None
    download_session = None
    if output:
        json_path = output + '/.staging/state.json'
        old_download_session = load_json(json_path, abort=False)
        if old_download_session and (not ids or ids == old_download_session['command']):
            download_session = old_download_session

    if ids and not download_session:
        validate_ids(ids, manifest)
        download_dispatch = DownloadDispatcher(json_path, container_version=tag)
        download_session = download_dispatch.download_manifest(repos, ids, manifest, output, API_URL, no_ssl_verify)

    dispatch = StatusScreenDispatcher()
    if not download_session:
        raise click.BadArgumentUsage("No id's provided and no session info found, aborting")
    if data_type == 'file':
        dispatch.file_table(download_session['file_data'], output, table_format)
    elif data_type == 'summary':
        dispatch.summary_table(download_session['file_data'], output, table_format)


@cli.command()
@click.argument('IDS', nargs=-1, required=False)
@click.option('--repos', '-r', multiple=True, type=RepoParam())
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              envvar='ICGCGET_OUTPUT')
@click.option('--cghub-key', type=click.STRING, envvar='ICGCGET_CGHUB_KEY')
@click.option('--cghub-path', envvar='ICGCGET_CGHUB_PATH')
@click.option('--ega-username', type=click.STRING, envvar='ICGCGET_EGA_USERNAME')
@click.option('--ega-password', type=click.STRING, envvar='ICGCGET_EGA_PASSWORD')
@click.option('--gdc-token', type=click.STRING, envvar='ICGCGET_GDC_TOKEN')
@click.option('--icgc-token', type=click.STRING, envvar='ICGCGET_ICGC_TOKEN')
@click.option('--pdc-key', type=click.STRING, envvar='ICGCGET_PDC_KEY')
@click.option('--pdc-secret', type=click.STRING, envvar='ICGCGET_PDC_SECRET')
@click.option('--pdc-path', envvar='ICGCGET_PDC_ACCESS')
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def check(ctx, repos, ids, manifest, output, cghub_key, cghub_path, ega_username, ega_password, gdc_token,
          icgc_token, pdc_key, pdc_secret, pdc_path, no_ssl_verify):
    logger = logging.getLogger('__log__')
    logger.debug(str(ctx.params))
    filter_repos(repos)
    tag = get_container_tag(ctx)
    dispatch = AccessCheckDispatcher()
    download_dispatch = DownloadDispatcher(tag)
    download_session = {'file_data': {}}
    if ('gdc' in repos or 'ega' in repos or 'pdc' in repos) and ids:
        download_session = download_dispatch.download_manifest(repos, ids, manifest, output, API_URL, no_ssl_verify)
    dispatch.access_checks(repos, download_session['file_data'], cghub_key, cghub_path, ega_username, ega_password,
                           gdc_token, icgc_token, pdc_key, pdc_secret, pdc_path, output, ctx.obj, API_URL,
                           no_ssl_verify)


@cli.command()
@click.option('--config', '-c', type=click.Path(), default=DEFAULT_CONFIG_FILE, envvar='ICGCGET_CONFIG')
def configure(config):
    default_dir = os.path.split(DEFAULT_CONFIG_FILE)[0]
    if config == DEFAULT_CONFIG_FILE and not os.path.exists(default_dir):
        os.umask(0000)
        os.mkdir(default_dir, 0777)
    dispatch = ConfigureDispatcher(config, DEFAULT_CONFIG_FILE)
    dispatch.configure(config)


@cli.command()
@click.option('--cghub-path', envvar='ICGCGET_CGHUB_PATH')
@click.option('--ega-path', envvar='ICGCGET_EGA_PATH')
@click.option('--gdc-path', envvar='ICGCGET_GDC_PATH')
@click.option('--icgc-path', envvar='ICGCGET_ICGC_PATH')
@click.option('--pdc-path', envvar='ICGCGET_PDC_PATH')
@click.pass_context
def version(ctx, cghub_path, ega_path, gdc_path, icgc_path, pdc_path):
    logger = logging.getLogger('__log__')
    logger.debug(str(ctx.params))
    tag = get_container_tag(ctx)
    versions_command(cghub_path, ega_path, gdc_path, icgc_path, pdc_path, ctx.obj, tag)


def main():
    cli()
    return 0

if __name__ == "__main__":
    main()
    sys.exit(0)
