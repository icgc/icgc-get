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
import psutil
import click
import yaml
from commands.versions import versions_command
from commands.reports import StatusScreenDispatcher
from commands.download import DownloadDispatcher
from commands.access_checks import AccessCheckDispatcher
from commands.utils import compare_ids, config_parse, validate_ids

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgcget', force_posix=True), 'config.yaml')
REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub', 'pdc']
VERSION = '0.5'


def logger_setup(logfile):
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)

    if logfile:
        if not os.path.isfile(logfile):
            print "Unable to find logfile {}: No file found".format(logfile)
        elif not os.access(logfile, os.W_OK | os.X_OK):
            print "Unable to write to logfile {}".format(logfile)
        else:
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler = logging.FileHandler(logfile)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)


def get_api_url(context_map):
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    elif context_map:
        api_url = context_map["portal_url"] + 'api/v1/'
    else:
        raise click.BadParameter("No API url specified by config file(portal:  url) or environmental variable" +
                                 " (ICGCGET_PORTAL_URL).")
    return api_url


@click.group()
@click.option('--config', default=DEFAULT_CONFIG_FILE)
@click.option('--logfile', default=None)
@click.pass_context
def cli(ctx, config, logfile):
    config_file = config_parse(config, DEFAULT_CONFIG_FILE)
    if config != DEFAULT_CONFIG_FILE and not config_file:
        raise click.Abort()
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
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              required=True)
@click.option('--cghub-access', type=click.STRING)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--cghub-transport-parallel', type=click.STRING, default='8')
@click.option('--ega-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-transport-parallel', type=click.STRING, default='1')
@click.option('--ega-udt', type=click.BOOL, default=False)
@click.option('--gdc-access', type=click.STRING)
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--gdc-transport-parallel', type=click.STRING, default='8')
@click.option('--gdc-udt', type=click.BOOL, default=False)
@click.option('--icgc-access', type=click.STRING)
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--icgc-transport-file-from', type=click.STRING, default='remote')
@click.option('--icgc-transport-parallel', type=click.STRING, default='8')
@click.option('--pdc-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-region', type=click.STRING, default='us-east-1')
@click.option('--pdc-transport-parallel', type=click.STRING, default='8')
@click.option('--yes-to-all', '-y', is_flag=True, default=False, help="Bypass all confirmation prompts")
@click.pass_context
def download(ctx, file_ids, repos, manifest, output,
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
    old_session_info = None
    if os.path.isfile(pickle_path):
        old_session_info = pickle.load(open(pickle_path, 'r+'))
        if psutil.pid_exists(old_session_info['pid']):
            raise click.Abort("Download currently in progress")
    if file_ids == 'resume':
        session_info = old_session_info
    else:
        validate_ids(file_ids, manifest)
        session_info = dispatch.download_manifest(repos, file_ids, manifest, output, yes_to_all, api_url)
    if old_session_info:
        session_info['object_ids'] = compare_ids(session_info['object_ids'], old_session_info['object_ids'], yes_to_all)
    pickle.dump(session_info, open(pickle_path, 'w'), pickle.HIGHEST_PROTOCOL)
    dispatch.download(session_info['object_ids'], staging, output,
                      cghub_access, cghub_path, cghub_transport_parallel,
                      ega_access, ega_path, ega_transport_parallel, ega_udt,
                      gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                      icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                      pdc_access, pdc_path, pdc_region, pdc_transport_parallel)
    os.remove(pickle_path)


@cli.command()
@click.argument('file-ids', nargs=-1, required=False)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True))
@click.option('--table-format', '-f', type=click.Choice(['tsv', 'pretty', 'json']), default='pretty')
@click.option('--data-type', '-t', type=click.Choice(['file', 'summary']), default='file')
@click.option('--override', '-o', is_flag=True, default=False, help="Bypass all prompts from cached session info")
@click.pass_context
def report(ctx, repos, file_ids, manifest, output, table_format, data_type, override):
    if not repos:
        raise click.BadOptionUsage("Must include prioritized repositories")
    api_url = get_api_url(ctx.default_map)
    pickle_path = output + '/.staging/state.pk'
    session_info = None
    download_dispatch = DownloadDispatcher(pickle_path)
    if file_ids:
        validate_ids(file_ids, manifest)
        session_info = download_dispatch.download_manifest(repos, file_ids, manifest, output, True, api_url)
    if os.path.isfile(pickle_path):
        old_session_info = pickle.load(open(pickle_path, 'r+'))
        if session_info:
            session_info['object_ids'] = compare_ids(session_info['object_ids'], old_session_info['object_ids'],
                                                     override)
        else:
            session_info = old_session_info
    dispatch = StatusScreenDispatcher()
    if not session_info:
        raise click.BadArgumentUsage("No id's provided and no session info found, Aborting")
    if data_type == 'file':
        dispatch.file_table(session_info['object_ids'], output, api_url, table_format)
    elif data_type == 'summary':
        dispatch.summary_table(session_info['object_ids'], output, api_url, table_format)


@cli.command()
@click.argument('file-ids', nargs=-1, required=False)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True))
@click.option('--cghub-access', type=click.STRING)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-access', type=click.STRING)
@click.option('--gdc-access', type=click.STRING)
@click.option('--icgc-access', type=click.STRING)
@click.option('--pdc-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True))
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-region', type=click.STRING, default='us-west-2')
@click.pass_context
def check(ctx, repos, file_ids, manifest, output,
          cghub_access, cghub_path, ega_access, gdc_access, icgc_access, pdc_access, pdc_path, pdc_region):
    if not repos:
        raise click.BadOptionUsage("Please specify repositories to check access to")
    if not file_ids:
        if 'gdc' in repos or 'cghub' in repos or 'pdc' in repos:
            raise click.BadOptionUsage("Access checks on Gdc, cghub, and pdc require a manifest or file ids to process")
    api_url = get_api_url(ctx.default_map)
    dispatch = AccessCheckDispatcher()
    dispatch.access_checks(repos, file_ids, manifest, cghub_access, cghub_path, ega_access, gdc_access, icgc_access,
                           pdc_access, pdc_path, pdc_region, output, api_url)


@cli.command()
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True, prompt=True)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              prompt=True)
@click.option('--cghub-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--ega-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
              prompt=True)
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--gdc-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--icgc-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--pdc-access', type=click.Path(exists=True, dir_okay=False, readable=True, resolve_path=True),
              prompt=True)
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--pdc-region', type=click.STRING, prompt=True)
def configure(repos, output, cghub_access, cghub_path, ega_access, ega_path, 
              gdc_access, gdc_path, icgc_access, icgc_path, pdc_access, pdc_path, pdc_region):
    conf_yaml = {'output': output, 'repos': repos,
                 'icgc': {'path': icgc_path, 'access': icgc_access},
                 'cghub': {'path': cghub_path, 'access': cghub_access},
                 'ega': {'path': ega_path, 'access': ega_access},
                 'gdc': {'path': gdc_path, 'access': gdc_access},
                 'pdc': {'path': pdc_path, 'access': pdc_access, 'region': pdc_region}}
    config_file = file(output + 'config.yaml', 'w')
    yaml.dump(conf_yaml, config_file)
    os.environ['ICGCGET_CONFIG'] = output + 'config.yaml'


@cli.command()
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
def version(cghub_path, ega_path, gdc_path, icgc_path, pdc_path):
    versions_command(cghub_path, ega_path, gdc_path, icgc_path, pdc_path, VERSION)


def main():
    cli(auto_envvar_prefix='ICGCGET')

if __name__ == "__main__":
    main()
