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
import pickle

import click
from icgcget.clients.utils import config_parse, get_api_url
from icgcget.commands.versions import versions_command
from icgcget.commands.status import StatusScreenDispatcher
from icgcget.commands.download import DownloadDispatcher

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')
REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub', 'pdc']
VERSION = '0.5'


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
@click.argument('file-ids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True))
@click.option('--cghub-access', type=click.STRING)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--cghub-transport-parallel', type=click.STRING)
@click.option('--ega-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-transport-parallel', type=click.STRING)
@click.option('--ega-udt', type=click.BOOL)
@click.option('--gdc-access', type=click.STRING)
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--gdc-transport-parallel', type=click.STRING)
@click.option('--gdc-udt', type=click.BOOL)
@click.option('--icgc-access', type=click.STRING)
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--icgc-transport-file-from', type=click.STRING)
@click.option('--icgc-transport-parallel', type=click.STRING)
@click.option('--pdc-access')
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-region', type=click.STRING)
@click.option('--pdc-transport-parallel', type=click.STRING)
@click.option('--yes-to-all', '-y', is_flag=True, default=False, help="Bypass all confirmation prompts")
@click.pass_context
def download(ctx, repos, file_ids, manifest, output,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_access, ega_path, ega_transport_parallel, ega_udt,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
             pdc_access, pdc_path, pdc_region, pdc_transport_parallel, yes_to_all):
    api_url = get_api_url(ctx.default_map)
    staging = output + '/.staging'
    if not os.path.exists(staging):
        os.umask(0000)
        os.mkdir(staging, 0777)
    pickle_path = output + '/.staging/state.pk'
    dispatch = DownloadDispatcher(pickle_path)
    object_ids = dispatch.download_manifest(repos, file_ids, manifest, staging, yes_to_all, api_url)

    if os.path.isfile(pickle_path):
        session_info = pickle.load(open(pickle_path, 'r+'))
        object_ids = dispatch.compare(object_ids, session_info, yes_to_all)
    pickle.dump(object_ids, open(pickle_path, 'w'), pickle.HIGHEST_PROTOCOL)
    dispatch.download(object_ids, staging, output,
                      cghub_access, cghub_path, cghub_transport_parallel,
                      ega_access, ega_path, ega_transport_parallel, ega_udt,
                      gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                      icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                      pdc_access, pdc_path, pdc_region, pdc_transport_parallel)
    os.remove(pickle_path)


@cli.command()
@click.argument('file-ids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS),  multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True))
@click.option('--cghub-access', type=click.STRING)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-access', type=click.STRING)
@click.option('--gdc-access', type=click.STRING)
@click.option('--icgc-access', type=click.STRING)
@click.option('--pdc-access', type=click.STRING)
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-region', type=click.STRING)
@click.option('--no-files', '-nf', is_flag=True, default=False, help="Do not show individual file information")
@click.pass_context
def status(ctx, repos, file_ids, manifest, output,
           cghub_access, cghub_path, ega_access, gdc_access, icgc_access, pdc_access, pdc_path, pdc_region,
           no_files):
    api_url = get_api_url(ctx.default_map)
    dispatch = StatusScreenDispatcher()
    gdc_ids, gnos_ids, pdc_ids, repo_list = dispatch.status_tables(repos, file_ids, manifest, api_url, no_files)
    dispatch.access_checks(repo_list, cghub_access, cghub_path, ega_access, gdc_access, icgc_access, pdc_access,
                           pdc_path, pdc_region, output, api_url, gnos_ids, gdc_ids, pdc_ids)


@cli.command()
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-access', type=click.STRING)
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def version(cghub_path, ega_access, ega_path, gdc_path, icgc_path, pdc_path):
    versions_command(cghub_path, ega_access, ega_path, gdc_path, icgc_path, pdc_path, VERSION)


def main():
    cli(auto_envvar_prefix='ICGCGET')

if __name__ == "__main__":
    main()
