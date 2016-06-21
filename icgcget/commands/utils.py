#!/usr/bin/python
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
import re
import json
import os
import psutil
import logging
import click
import yaml
from icgcget.clients import errors
from icgcget.clients import portal_client
from icgcget.clients.utils import normalize_keys, flatten_dict


def api_error_catch(self, func, *args):
    try:
        return func(*args)
    except errors.ApiError as ex:
        self.logger.error(ex.message)
        raise click.Abort


def check_access(self, access, name, path="Default", password="Default", secret_key="Default", udt=True):
    if access is None:
        self.logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter("Please provide credentials for {}".format(name))
    if password is None:
        self.logger.error("No password provided for the {} repository".format(name))
        raise click.BadParameter("Please provide a password to the {} download client".format(name))
    if secret_key is None:
        self.logger.error("No secret key provided for the {} repository".format(name))
        raise click.BadParameter("Please provide a secret key for {}".format(name))
    if not isinstance(udt, bool):
        raise click.BadParameter("UDT flag must be in boolean format")
    if path is None:
        self.logger.error("Path to {} download client not provided.".format(name))
        raise click.BadParameter("Please provide a path to the {} download client".format(name))
    if not os.path.isfile(path):
        self.logger.error("Path to {} download client cannot be resolved.".format(name))
        raise click.BadParameter("Please provide a complete path to the {} download client".format(name))


def compare_ids(current_session, old_session, override):
    updated_session = {}
    for repo in current_session:
        updated_session[repo] = {}
        if repo not in old_session:
            if override_prompt(override):
                return current_session
        for fi_id in current_session[repo]:
            if fi_id in old_session[repo]:
                if old_session[repo][fi_id]['state'] != "Finished":
                    updated_session[repo][fi_id] = current_session[repo][fi_id]
            else:

                if override_prompt(override):
                    return current_session
    return updated_session


def config_errors(message, default):
    if default:
        return {}
    else:
        print message
        raise click.Abort()


def config_parse(filename, default_filename, empty_ok=False):
    default = filename == default_filename
    try:
        config_text = open(filename, 'r')
    except IOError as ex:
        config_text = config_errors("Config file {0} not found: {1}".format(filename, ex.strerror), default)
    try:
        yaml.SafeLoader.add_constructor("tag:yaml.org,2002:python/unicode", constructor)
        config_temp = yaml.safe_load(config_text)
        if config_temp:
            config_download = flatten_dict(normalize_keys(config_temp))
            config = {'download': config_download, 'report': config_download, 'version': config_download,
                      'check': config_download}
            if 'logfile' in config_temp:
                config['logfile'] = config_temp['logfile']
        elif empty_ok:
            return {}
        else:
            config = config_errors("Config file {} is an empty file.".format(filename), default)
    except yaml.YAMLError:
        config = config_errors("Failed to parse config file {}.  Config must be in YAML format.".format(filename),
                               default)
    return config


def constructor(loader, node):
    return node.value


def filter_manifest_ids(self, manifest_json, repos):
    fi_ids = []  # Function to return a list of unique file ids from a manifest.  Throws error if not unique
    for repo_info in manifest_json["entries"]:
        if repo_info["repo"] in repos:
            for file_info in repo_info["files"]:
                if file_info["id"] in fi_ids:
                    self.logger.error("Supplied manifest has repeated file identifiers.  Please specify a " +
                                      "list of repositories to prioritize")
                    raise click.Abort
                else:
                    fi_ids.append(file_info["id"])
    if not fi_ids:
        self.logger.warning("No files found on specified repositories")
        raise click.Abort
    return fi_ids


def get_entities(self, object_ids, api_url, verify):
    file_ids = []
    for repo in object_ids:
        file_ids.extend(object_ids[repo].keys())
    portal = portal_client.IcgcPortalClient(verify)
    entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
    return entities


def get_manifest_json(self, file_ids, api_url, repos, portal):
    if len(file_ids) > 1:
        self.logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
        raise click.BadArgumentUsage("Multiple manifest files specified.")
    manifest_json = api_error_catch(self, portal.get_manifest_id, file_ids[0], api_url, repos)
    return manifest_json


def load_json(json_path, abort=True):
    if os.path.isfile(json_path):
        try:
            old_session_info = json.load(open(json_path, 'r+'))
            if abort and psutil.pid_exists(old_session_info['pid']):
                raise click.Abort("Download currently in progress")
            return old_session_info
        except ValueError:
            logger = logging.getLogger('__log__')
            logger.warning("Corrupted download state found.  Cleaning...")
            os.remove(json_path)
    return None


def match_repositories(self, repos, copies):
    for repository in repos:
        for copy in copies["fileCopies"]:
            if repository == copy["repoCode"]:
                return repository, copy
    self.logger.error("File %s not found on repositories %s", copies["id"], repos)
    raise click.Abort


def override_prompt(override):
    if override:
        return True
    if click.confirm("Previous session data does not match current command.  Ok to overwrite previous session info?"):
        return True
    else:
        raise click.Abort


def validate_ids(ids, manifest):
    if manifest:
        if not re.match(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', ids[0]):
            raise click.BadArgumentUsage(message="Bad Manifest ID: passed argument {} isn't in uuid format".format(ids))
    else:
        for fi_id in ids:
            if not re.findall(r'FI\d*', fi_id):
                if re.match(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', fi_id):
                    raise click.BadArgumentUsage(message="Bad FI ID: passed argument {}".format(fi_id) +
                                                 "is in UUID format.  If you intended to use a manifest," +
                                                 "add the -m tag.")
                raise click.BadArgumentUsage(message="Bad FI ID: passed argument {}".format(fi_id) +
                                             "isn't in FI00000 format")
