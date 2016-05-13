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
from tabulate import tabulate
import click

import psutil
from base64 import b64decode

from clients.ega import ega_client
from clients.gdc import gdc_client
from clients.gnos import gt_client
from clients.icgc import icgc_api
from clients.icgc import icgc_client
from utils import file_size, config_parse, match_repositories

REPOS = ['collaboratory', 'aws-virginia', 'ega', 'gdc', 'cghub']  # Updated for codes used by api

DEFAULT_CONFIG_FILE = os.path.join(click.get_app_dir('icgc-get', force_posix=True), 'config.yaml')
global logger


def logger_setup(logfile):
    global logger
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


def check_code(client, code):
    if code != 0:
        logger.error("{} client exited with a nonzero error code {}.".format(client, code))
        raise click.ClickException("Please check client output for error messages")


def check_access(access, name):
    if access is None:
        logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter("Please provide credentials for {}".format(name))


def size_check(size, override, output):
    free = psutil.disk_usage(output)[2]
    if free > size and not override:
        if not click.confirm("Ok to download {0}s of files? There is {1}s of free space in {2}".format(''.join(
                                                                                                       file_size(size)),
                                                                                                       ''.join(
                                                                                                       file_size(free)),
                                                                                                       output)):
            logger.info("User aborted download")
            raise click.Abort
    elif free <= size:
        logger.warning("Not enough space detected for download of {0}. {1} of space in {2}".format(''.join(
                                                                                                   file_size(size)),
                                                                                                   ''.join(
                                                                                                   file_size(free)),
                                                                                                   output))
        raise click.Abort


def access_response(result, repo):
    if result:
        logger.info("Valid access to the " + repo)
    else:
        logger.info("Invalid access to the " + repo)


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
@click.option('--ega-password', type=click.STRING)
@click.option('--ega-path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--ega-transport-parallel', type=click.STRING)
@click.option('--ega-udt', type=click.BOOL)
@click.option('--ega-username', type=click.STRING)
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
             ega_password, ega_path, ega_transport_parallel, ega_udt, ega_username,
             gdc_access, gdc_path, gdc_transport_parallel, gdc_udt,
             icgc_access, icgc_path, icgc_transport_file_from, icgc_transport_parallel, yes_to_all):
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    else:
        api_url = ctx.default_map["portal_url"] + ctx.default_map["portal_api"]
    object_ids = {}

    size = 0
    if manifest:
        if len(fileids) > 1:
            logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
            raise click.BadArgumentUsage("Multiple manifest files specified.")
        try:
            manifest_json = icgc_api.get_manifest_id(fileids[0], api_url, repos)
        except RuntimeError:
            raise click.Abort
    else:
        try:
            manifest_json = icgc_api.get_manifest(fileids, api_url, repos)
        except RuntimeError:
            raise click.Abort
    if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
        fi_ids = []
        for repo_info in manifest_json["entries"]:
            if repo_info["repo"] in REPOS:
                for file_info in repo_info["files"]:
                    if file_info["id"] in fi_ids:
                        logger.error("Supplied manifest has repeated file identifiers.  Please specify a " +
                                     "")
                        raise click.Abort
                    else:
                        fi_ids.append(file_info["id"])

    for repo_info in manifest_json["entries"]:
        repo = repo_info["repo"]
        if repo == 'ega':
            object_ids['ega'] = []
            for file_info in repo_info["files"]:
                object_ids[repo].append(file_info["repoFileId"])
                size += file_info["size"]
        else:
            object_ids[repo] = b64decode(repo_info["content"])
            for file_info in repo_info["files"]:
                size += file_info["size"]
    size_check(size, yes_to_all, output)

    if 'cghub' in object_ids and object_ids['cghub']:
        check_access(cghub_access, 'cghub')
        if manifest:
            code = gt_client.genetorrent_manifest_call(object_ids['cghub'], cghub_access, cghub_path,
                                                       cghub_transport_parallel, output)
        else:
            code = gt_client.genetorrent_call(object_ids['cghub'], cghub_access, cghub_path,
                                              cghub_transport_parallel, output)
        check_code('Cghub', code)

    if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
        check_access(icgc_access, 'icgc')
        if manifest:
            code = icgc_client.icgc_manifest_call(object_ids['aws-virginia'], icgc_access, icgc_path,
                                                  icgc_transport_file_from, icgc_transport_parallel, output, 'aws')
        else:
            code = icgc_client.icgc_call(object_ids['aws-virginia'], icgc_access, icgc_path, icgc_transport_file_from,
                                         icgc_transport_parallel, output, 'aws')
        check_code('Icgc', code)

    if 'ega' in object_ids and object_ids['ega']:
        if ega_username is None or ega_password is None:
            check_access(None, 'ega')
        else:
            if ega_transport_parallel != '1':
                logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                               "downloads.  This option is not recommended.")
            code = ega_client.ega_call(object_ids['ega'], ega_username, ega_password, ega_path,
                                       ega_transport_parallel, ega_udt, output)
            check_code('Ega', code)



    if 'collaboratory' in object_ids and object_ids['collaboratory']:
        check_access(icgc_access, 'icgc')
        if manifest:
            code = icgc_client.icgc_manifest_call(object_ids['collaboratory'], icgc_access, icgc_path,
                                                  icgc_transport_file_from, icgc_transport_parallel, output, 'collab')
        else:
            code = icgc_client.icgc_call(object_ids['collaboratory'], icgc_access, icgc_path,
                                         icgc_transport_file_from, icgc_transport_parallel, output, 'collab')
        check_code('Icgc', code)

    if 'gdc' in object_ids and object_ids['gdc']:
        check_access(gdc_access, 'gdc')
        if manifest:
            code = gdc_client.gdc_manifest_call(object_ids['gdc'], gdc_access, gdc_path, output, gdc_udt,
                                                gdc_transport_parallel)
        else:
            code = gdc_client.gdc_call(object_ids['gdc'], gdc_access, gdc_path, output, gdc_udt, gdc_transport_parallel)
        check_code('Gdc', code)


@cli.command()
@click.argument('fileids', nargs=-1, required=True)
@click.option('--repos', '-r', type=click.Choice(REPOS),  multiple=True)
@click.option('--manifest', '-m', is_flag=True, default=False)
@click.option('--cghub-access', type=click.STRING)
@click.option('--ega-username', type=click.STRING)
@click.option('--ega-password', type=click.STRING)
@click.option('--gdc-access', type=click.STRING)
@click.option('--icgc-access', type=click.STRING)
@click.pass_context
def dryrun(ctx, repos, fileids, manifest, cghub_access,
           ega_username, ega_password, gdc_access,
           icgc_access):

    repo_list = []
    gdc_ids = []
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    else:
        api_url = ctx.default_map["portal_url"] + ctx.default_map["portal_api"]
    total_size = 0
    table = [["", "Size", "Unit", "Repo"]]
    if manifest:
        if len(fileids) > 1:
            logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
            raise click.BadArgumentUsage("Multiple manifest files specified.")
        try:
            manifest_json = icgc_api.get_manifest_id(fileids[0], api_url, repos)
        except RuntimeError:
            raise click.Abort

        fi_ids = []
        for repo_info in manifest_json["entries"]:
            if repo_info["repo"] in REPOS:
                for file_info in repo_info["files"]:
                    if file_info["id"] in fi_ids:
                        logger.error("Supplied manifest has repeated file identifiers.  Please specify repositries")
                        raise click.Abort
                    else:
                        fi_ids.append(file_info["id"])
        else:
            fileids = fi_ids
    repo_sizes = {}
    if not repos:
        raise click.BadOptionUsage("Must include prioritized repositories")
    for repository in repos:
        repo_sizes[repository] = 0
    total_size = 0
    entities = icgc_api.get_metadata_bulk(fileids, api_url)
    for entity in entities:
        size = entity["fileCopies"][0]["fileSize"]
        total_size += size
        repository, copy = match_repositories(repos, entity)
        filesize = file_size(size)
        table.append([entity["id"], filesize[0], filesize[1], repository])
        if repository == "gdc":
            gdc_ids.append(entity["dataBundle"]["dataBundleId"])
        repo_sizes[repository] += size
    for repo in repo_sizes:
        filesize = file_size(repo_sizes[repo])
        table.append([repo, filesize[0], filesize[1], ''])
        repo_list.append(repo)
    filesize = file_size(total_size)
    table.append(["Total Size", filesize[0], filesize[1], ""])
    logger.info(tabulate(table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))

    if "collaboratory" in repo_list:
        check_access(icgc_access, "icgc")
        access_response(icgc_client.icgc_access_check(icgc_access, "collab", api_url), "Collaboratory.")
    if "aws-virginia" in repo_list:
        check_access(icgc_access, "icgc")
        access_response(icgc_client.icgc_access_check(icgc_access, "aws", api_url), "Amazon Web server.")
    if 'ega' in repo_list:
        if ega_username is None or ega_password is None:
            check_access(None, 'ega')
            access_response(ega_client.ega_access_check(ega_username, ega_password), "ega.")
        else:
            access_response(ega_client.ega_access_check(ega_username, ega_password), "ega.")
    if 'gdc' in repo_list and gdc_ids:  # We don't get general access credentials to gdc, can't check without files.
        check_access(gdc_access, 'gdc')
        access_response(gdc_client.gdc_access_check(gdc_access, gdc_ids), "gdc files specified.")
    if 'cghub' in repo_list:
        check_access(cghub_access, 'cghub')


def main():
    cli(auto_envvar_prefix='ICGCGET')

if __name__ == "__main__":
    main()
