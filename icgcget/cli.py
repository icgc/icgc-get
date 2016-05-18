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
import psutil
from clients.errors import ApiError
from utils import config_parse, get_api_url, file_size
import dispatcher

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')
REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']


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


def match_repositories(repos, copies):
    logger = logging.getLogger('__log__')
    for repository in repos:
        for copy in copies["fileCopies"]:
            if repository == copy["repoCode"]:
                return repository, copy
    logger.error("File {} not found on repositories {}".format(copies["id"], repos))
    raise click.Abort


def filter_manifest_ids(manifest_json):
    logger = logging.getLogger('__log__')
    fi_ids = []  # Function to return a list of unique  file ids from a manifest.  Throws error if not unique
    for repo_info in manifest_json["entries"]:
        if repo_info["repo"] in REPOS:
            for file_info in repo_info["files"]:
                if file_info["id"] in fi_ids:
                    logger.error("Supplied manifest has repeated file identifiers.  Please specify a " +
                                 "list of repositories to prioritize")
                    raise click.Abort
                else:
                    fi_ids.append(file_info["id"])
    if not fi_ids:
        logger.warning("Files on manifest are not found on specified repositories")
        raise click.Abort
    return fi_ids


def check_code(client, code):
    logger = logging.getLogger('__log__')
    if code != 0:
        logger.error("{} client exited with a nonzero error code {}.".format(client, code))
        raise click.ClickException("Please check client output for error messages")


def check_access(access, name):
    logger = logging.getLogger('__log__')
    if access is None:
        logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter("Please provide credentials for {}".format(name))


def size_check(size, override, output):
    logger = logging.getLogger('__log__')
    free = psutil.disk_usage(output)[2]
    if free > size and not override:
        if not click.confirm("Ok to download {0}s of files?  ".format(''.join(file_size(size))) +
                             "There is {}s of free space in {}".format(''.join(file_size(free)), output)):
            logger.info("User aborted download")
            raise click.Abort
    elif free <= size:
        logger.error("Not enough space detected for download of {0}.".format(''.join(file_size(size))) +
                     "{} of space in {}".format(''.join(file_size(free)), output))
        raise click.Abort


def access_response(result, repo):
    logger = logging.getLogger('__log__')
    if result:
        logger.info("Valid access to the " + repo)
    else:
        logger.info("Invalid access to the " + repo)


def api_error_catch(func, *args):
    logger = logging.getLogger('__log__')
    try:
        return func(*args)
    except ApiError as e:
        logger.error(e.message)
        raise click.Abort


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
@click.option('--yes-to-all', '-y', is_flag=True, default=False, help="Bypass all confirmation prompts")
@click.pass_context
def download(ctx, repos, fileids, manifest, output,
             cghub_access, cghub_path, cghub_transport_parallel,
             ega_access, ega_path, ega_transport_parallel, ega_udt,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel, yes_to_all):
    api_url = get_api_url(ctx.default_map)
    dispatcher.download(repos, fileids, manifest, output,
                        cghub_access, cghub_path, cghub_transport_parallel,
                        ega_access, ega_path, ega_transport_parallel, ega_udt,
                        gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
                        icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel, yes_to_all, api_url)


@cli.command()
@click.argument('fileids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS),  multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--output', type=click.Path(exists=True, writable=True, file_okay=False, resolve_path=True))
@click.option('--cghub-access', type=click.STRING)
@click.option('--cghub-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-access', type=click.STRING)
@click.option('--gdc-access', type=click.STRING)
@click.option('--icgc-access', type=click.STRING)
@click.option('--no-files', '-nf', is_flag=True, default=False, help="Do not show individual file information")
@click.pass_context
def status(ctx, repos, fileids, manifest, output,
           cghub_access, cghub_path, ega_access, gdc_access, icgc_access,
           no_files):
    api_url = get_api_url(ctx.default_map)
    dispatcher.status(repos, fileids, manifest, output, api_url,
                      cghub_access, cghub_path, ega_access, gdc_access, icgc_access,
                      no_files)


def main():
    cli(auto_envvar_prefix='ICGCGET')

if __name__ == "__main__":
    main()
