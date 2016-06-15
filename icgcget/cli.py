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


def get_api_url(context_map):
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    elif context_map:
        api_url = context_map["portal_url"] + 'api/v1/'
    else:
        api_url = "https://www.icgc.com/api/v1"
    return api_url


@click.group()
@click.option('--config', default=DEFAULT_CONFIG_FILE, envvar='ICGCGET_CONFIG')
@click.option('--logfile', default=None, envvar='ICGCGET_LOGFILE')
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
@click.argument('ids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              required=True, envvar='ICGCGET_OUTPUT')
@click.option('--cghub-access', type=click.STRING, envvar='ICGCGET_CGHUB_ACCESS')
@click.option('--cghub-path', type=click.STRING, envvar='ICGCGET_CGHUB_PATH')
@click.option('--cghub-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_CGHUB_TRANSPORT_PARALLEL')
@click.option('--ega-username', type=click.STRING, envvar='ICGCGET_EGA_USERNAME')
@click.option('--ega-password', type=click.STRING, envvar='ICGCGET_EGA_PASSWORD')
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_EGA_PATH')
@click.option('--ega-transport-parallel', type=click.STRING, default='1', envvar='ICGCGET_EGA_TRANSPORT_PARALLEL')
@click.option('--ega-udt', type=click.BOOL, default=False, envvar='ICGCGET_EGA_UDT')
@click.option('--gdc-access', type=click.STRING, envvar='ICGCGET_GDC_ACCESS')
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_GDC_PATH')
@click.option('--gdc-transport-parallel', type=click.STRING, default='8')
@click.option('--gdc-udt', type=click.BOOL, default=False, envvar='ICGCGET_GDC_UDT')
@click.option('--icgc-access', type=click.STRING, envvar='ICGCGET_ICGC_ACCESS')
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              envvar='ICGCGET_CGHUB_ACCESS')
@click.option('--icgc-transport-file-from', type=click.STRING, default='remote',
              envvar='ICGCGET_ICGC_TRANSPORT_FILE_FROM')
@click.option('--icgc-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_PDC_TRANSPORT_PARALLEL')
@click.option('--pdc-key', type=click.STRING, envvar='ICGCGET_PDC_KEY')
@click.option('--pdc-secret', type=click.STRING, envvar='ICGCGET_PDC_SECRET')
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_PDC_PATH')
@click.option('--pdc-transport-parallel', type=click.STRING, default='8', envvar='ICGCGET_PDC_TRANSPORT_PARALLEL')
@click.option('--override', '-o', is_flag=True, default=True, help="Bypass all confirmation prompts")
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def download(ctx, ids, repos, manifest, output,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
             pdc_key, pdc_secret, pdc_path, pdc_transport_parallel, override, no_ssl_verify):
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
    if ids == 'resume':
        session_info = old_session_info
    else:
        validate_ids(ids, manifest)
        session_info = dispatch.download_manifest(repos, ids, manifest, output, api_url, no_ssl_verify)
    if old_session_info:
        session_info['object_ids'] = compare_ids(session_info['object_ids'], old_session_info['object_ids'], override)
    pickle.dump(session_info, open(pickle_path, 'w', 0777), pickle.HIGHEST_PROTOCOL)
    dispatch.download(session_info, staging, output,
                      cghub_access, cghub_path, cghub_transport_parallel,
                      ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                      gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                      icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                      pdc_key, pdc_secret, pdc_path, pdc_transport_parallel)
    os.remove(pickle_path)


@cli.command()
@click.argument('ids', nargs=-1, required=False)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              envvar='ICGCGET_OUTPUT')
@click.option('--table-format', '-f', type=click.Choice(['tsv', 'pretty', 'json']), default='pretty')
@click.option('--data-type', '-t', type=click.Choice(['file', 'summary']), default='file')
@click.option('--override', '-o', is_flag=True, default=False, help="Bypass all prompts from cached session info")
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def report(ctx, repos, ids, manifest, output, table_format, data_type, override, no_ssl_verify):
    if not repos:
        raise click.BadOptionUsage("Must include prioritized repositories")
    api_url = get_api_url(ctx.default_map)
    pickle_path = output + '/.staging/state.pk'
    session_info = None
    download_dispatch = DownloadDispatcher(pickle_path)
    if ids:
        validate_ids(ids, manifest)
        session_info = download_dispatch.download_manifest(repos, ids, manifest, output, api_url, no_ssl_verify)
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
        dispatch.file_table(session_info['object_ids'], output, api_url, table_format, no_ssl_verify)
    elif data_type == 'summary':
        dispatch.summary_table(session_info['object_ids'], output, api_url, table_format, no_ssl_verify,)


@cli.command()
@click.argument('ids', nargs=-1, required=False)
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True),
              envvar='ICGCGET_OUTPUT')
@click.option('--cghub-access', type=click.STRING, envvar='ICGCGET_CGHUB_ACCESS')
@click.option('--cghub-path', type=click.STRING, envvar='ICGCGET_CGHUB_PATH')
@click.option('--ega-username', type=click.STRING, envvar='ICGCGET_EGA_USERNAME')
@click.option('--ega-password', type=click.STRING, envvar='ICGCGET_EGA_PASSWORD')
@click.option('--gdc-access', type=click.STRING, envvar='ICGCGET_GDC_ACCESS')
@click.option('--icgc-access', type=click.STRING, envvar='ICGCGET_ICGC_ACCESS')
@click.option('--pdc-key', type=click.STRING, envvar='ICGCGET_PDC_KEY')
@click.option('--pdc-secret', type=click.STRING, envvar='ICGCGET_PDC_SECRET')
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              envvar='ICGCGET_PDC_ACCESS')
@click.option('--no-ssl-verify', is_flag=True, default=True, help="Do not verify ssl certificates")
@click.pass_context
def check(ctx, repos, ids, manifest, output, cghub_access, cghub_path, ega_username, ega_password, gdc_access,
          icgc_access, pdc_key, pdc_secret, pdc_path, no_ssl_verify):
    if not repos:
        raise click.BadOptionUsage("Please specify repositories to check access to")
    if not ids:
        if 'gdc' in repos or 'cghub' in repos or 'pdc' in repos:
            raise click.BadOptionUsage("Access checks on Gdc, cghub, and pdc require a manifest or file ids to process")
    api_url = get_api_url(ctx.default_map)
    dispatch = AccessCheckDispatcher()
    dispatch.access_checks(repos, ids, manifest, cghub_access, cghub_path, ega_username, ega_password, gdc_access,
                           icgc_access, pdc_key, pdc_secret, pdc_path, output, api_url, no_ssl_verify)


@cli.command()
@click.option('--repos', '-r', type=click.Choice(REPOS), multiple=True, prompt=True)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True), prompt=True)
@click.option('--cghub-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--ega-username', type=click.STRING, prompt=True)
@click.option('--ega-password', type=click.STRING, prompt=True)
@click.option('--ega-path', type=click.STRING, prompt=True)
@click.option('--gdc-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--icgc-access', type=click.STRING, prompt=True, hide_input=True)
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
@click.option('--pdc-key', type=click.STRING, prompt=True)
@click.option('--pdc-secret-key', type=click.STRING, prompt=True)
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), prompt=True)
def configure(repos, output, cghub_access, cghub_path, ega_username, ega_password, ega_path, gdc_access, gdc_path,
              icgc_access, icgc_path, pdc_key, pdc_secret_key, pdc_path):
    conf_yaml = {'output': output, 'repos': repos,
                 'icgc': {'path': icgc_path, 'access': icgc_access},
                 'cghub': {'path': cghub_path, 'access': cghub_access},
                 'ega': {'path': ega_path, 'username': ega_username, 'password': ega_password},
                 'gdc': {'path': gdc_path, 'access': gdc_access},
                 'pdc': {'path': pdc_path, 'key': pdc_key, 'secret': pdc_secret_key}}
    config_file = file(output + 'config.yaml', 'w')
    yaml.dump(conf_yaml, config_file)
    os.environ['ICGCGET_CONFIG'] = output + 'config.yaml'


@cli.command()
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              envvar='ICGCGET_CGHUB_PATH')
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_EGA_PATH')
@click.option('--gdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_GDC_PATH')
@click.option('--icgc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True),
              envvar='ICGCGET_ICGC_PATH')
@click.option('--pdc-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True), envvar='ICGCGET_PDC_PATH')
def version(cghub_path, ega_path, gdc_path, icgc_path, pdc_path):
    versions_command(cghub_path, ega_path, gdc_path, icgc_path, pdc_path, VERSION)


def main():
    cli()

if __name__ == "__main__":
    main()
