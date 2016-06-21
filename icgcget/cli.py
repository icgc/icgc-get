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
import json
import click

from commands.versions import versions_command
from commands.reports import StatusScreenDispatcher
from commands.download import DownloadDispatcher
from commands.access_checks import AccessCheckDispatcher
from commands.utils import compare_ids, config_parse, validate_ids, load_json
from commands.configure import ConfigureDispatcher

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')
REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub', 'pdc']
VERSION = '0.2.2'
API_URL = "https://staging.dcc.icgc.org/api/v1/"


def logger_setup(logfile):
    logger = logging.getLogger('__log__')
    logger.setLevel(logging.DEBUG)

    if logfile:
        try:
            open(logfile, 'w+')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler = logging.FileHandler(logfile)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except IOError as ex:
            if not ex.errno == 2:
                print "Unable to write to logfile {}".format(logfile)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)


def validate_repos(repos):
    if not repos or repos.count(None) == len(repos):
        raise click.BadOptionUsage("Must include prioritized repositories")
    for repo in repos:
        if repo not in REPOS:
            if not repo:
                raise click.BadOptionUsage("Null entry in list of repositories")
            elif len(repo) == 1:
                raise click.BadOptionUsage("Repos need to be entered in list format.")
            else:
                raise click.BadOptionUsage("Invalid repo {0}.  Valid repositories are {1}".format(repo, REPOS))


@click.group()
@click.option('--config', default=DEFAULT_CONFIG_FILE, envvar='ICGCGET_CONFIG')
@click.option('--logfile', default=None, envvar='ICGCGET_LOGFILE')
@click.pass_context
def cli(ctx, config, logfile):
    if ctx.invoked_subcommand != 'configure':
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
@click.argument('ids', nargs=-1, required=True)
@click.option('--repos', '-r', multiple=True)
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
def download(ids, repos, manifest, output,
             cghub_key, cghub_path, cghub_transport_parallel,
             ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
             gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
             pdc_key, pdc_secret, pdc_path, pdc_transport_parallel, override, no_ssl_verify):
    validate_repos(repos)
    staging = output + '/.staging'
    if not os.path.exists(staging):
        os.umask(0000)
        os.mkdir(staging, 0777)
    json_path = output + '/.staging/state.json'

    old_session_info = load_json(json_path)
    dispatch = DownloadDispatcher(json_path)
    if old_session_info and ids == old_session_info['command']:
            session_info = old_session_info
    else:
        validate_ids(ids, manifest)
        session_info = dispatch.download_manifest(repos, ids, manifest, output, API_URL, no_ssl_verify)
    if old_session_info:
        session_info['object_ids'] = compare_ids(session_info['object_ids'], old_session_info['object_ids'], override)
    json.dump(session_info, open(json_path, 'w', 0777))
    dispatch.download(session_info, staging, output,
                      cghub_key, cghub_path, cghub_transport_parallel,
                      ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                      gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
                      icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                      pdc_key, pdc_secret, pdc_path, pdc_transport_parallel)
    os.remove(json_path)


@cli.command()
@click.argument('ids', nargs=-1, required=False)
@click.option('--repos', '-r', multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              envvar='ICGCGET_OUTPUT')
@click.option('--table-format', '-f', type=click.Choice(['tsv', 'pretty', 'json']), default='pretty')
@click.option('--data-type', '-t', type=click.Choice(['file', 'summary']), default='file')
@click.option('--override', '-o', is_flag=True, default=False, help="Bypass all prompts from cached session info")
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
def report(repos, ids, manifest, output, table_format, data_type, no_ssl_verify):
    validate_repos(repos)
    json_path = None
    session_info = None
    if output:
        json_path = output + '/.staging/state.json'
        old_session_info = load_json(json_path, abort=False)
        if old_session_info and (not ids or ids == old_session_info['command']):
            session_info = old_session_info

    if ids and not session_info:
        validate_ids(ids, manifest)
        download_dispatch = DownloadDispatcher(json_path)
        session_info = download_dispatch.download_manifest(repos, ids, manifest, output, API_URL, no_ssl_verify)
    dispatch = StatusScreenDispatcher()
    if not session_info:
        raise click.BadArgumentUsage("No id's provided and no session info found, Aborting")
    if data_type == 'file':
        dispatch.file_table(session_info['object_ids'], output, API_URL, table_format, no_ssl_verify)
    elif data_type == 'summary':
        dispatch.summary_table(session_info['object_ids'], output, API_URL, table_format, no_ssl_verify,)


@cli.command()
@click.argument('ids', nargs=-1, required=False)
@click.option('--repos', '-r', multiple=True)
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
def check(repos, ids, manifest, output, cghub_key, cghub_path, ega_username, ega_password, gdc_token,
          icgc_token, pdc_key, pdc_secret, pdc_path, no_ssl_verify):
    validate_repos(repos)
    dispatch = AccessCheckDispatcher()
    dispatch.access_checks(repos, ids, manifest, cghub_key, cghub_path, ega_username, ega_password, gdc_token,
                           icgc_token, pdc_key, pdc_secret, pdc_path, output, API_URL, no_ssl_verify)


@cli.command()
@click.option('--config', '-c', type=click.Path(), default=DEFAULT_CONFIG_FILE, envvar='ICGCGET_CONFIG')
@click.option('--no-paths', is_flag=True, default=False, help="Do not write path values")
def configure(config, no_paths):
    dispatch = ConfigureDispatcher(config, DEFAULT_CONFIG_FILE)
    dispatch.configure(config)


@cli.command()
@click.option('--cghub-path', envvar='ICGCGET_CGHUB_PATH')
@click.option('--ega-path', envvar='ICGCGET_EGA_PATH')
@click.option('--gdc-path', envvar='ICGCGET_GDC_PATH')
@click.option('--icgc-path', envvar='ICGCGET_ICGC_PATH')
@click.option('--pdc-path', envvar='ICGCGET_PDC_PATH')
def version(cghub_path, ega_path, gdc_path, icgc_path, pdc_path):
    versions_command(cghub_path, ega_path, gdc_path, icgc_path, pdc_path, VERSION)


def main():
    cli()

if __name__ == "__main__":
    main()
