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
import re
import json
import os
import logging
import psutil
import click
import yaml
import signal
from icgcget.clients import errors
from icgcget.clients.utils import normalize_keys, flatten_dict
from icgcget.params import ICGC_REPOS


def api_error_catch(self, func, *args):
    try:
        return func(*args)
    except errors.ApiError as ex:
        self.logger.error(ex.message)
        raise click.Abort


def check_access(self, access, name, docker=False, path='Default', password='Default', secret_key='Default', udt=True):
    """
    Verifies if path and access parameters have been provided and that paths are valid.
    :param self:
    :param access:
    :param name:
    :param docker:
    :param path:
    :param password:
    :param secret_key:
    :param udt:
    :return:
    """
    if access is None:
        self.logger.error('No credentials provided for the {} repository'.format(name))
        raise click.BadParameter('Please provide credentials for {}'.format(name))
    if password is None:
        self.logger.error('No password provided for the {} repository'.format(name))
        raise click.BadParameter('Please provide a password to the {} download client'.format(name))
    if secret_key is None:
        self.logger.error('No secret key provided for the {} repository'.format(name))
        raise click.BadParameter('Please provide a secret key for {}'.format(name))
    if not isinstance(udt, bool):
        raise click.BadParameter('UDT flag must be in boolean format')
    if path is None:
        if name in ICGC_REPOS:
            self.logger.error('Path to the score-client is not provided.')
            raise click.BadParameter('Please provide a path to the score-client')
        elif 'pcawg' in name:
            self.logger.error('Path to the gtdownload client is not provided.')
            raise click.BadParameter('Please provide a path to the gtdownload client')
        else:
            self.logger.error('Path to the download client for {} is not provided.'.format(name))
            raise click.BadParameter('Please provide a path to the {} download client'.format(name))
    if not os.path.isfile(path) and not docker and path != 'Default':
        if name in ICGC_REPOS:
            self.logger.error('Path "{}" to the score-client cannot be resolved.'.format(path))
            raise click.BadParameter('Please provide a complete path to the score-client')
        elif 'pcawg' in name:
            self.logger.error('Path to the gtdownload cannot be resolved.')
            raise click.BadParameter('Please provide a complete path to the gtdownload client')
        else:
            self.logger.error('Path "{0}" to {1} download client cannot be resolved.'.format(path, name))
            raise click.BadParameter('Please provide a complete path to the {} download client'.format(name))


def compare_ids(current_session, old_session, override):
    """
    Compares manifest of state.json to manifest retrieved from api and strips out any files that already finished.
    If current session does not match old session, the process is stopped
    :param current_session:
    :param old_session:
    :param override:
    :return:
    """
    updated_session = {}
    for repo in current_session:
        updated_session[repo] = {}
        if repo not in old_session:
            if override_prompt(override):
                return current_session  # if entire repo is new, wipe old session data
        for fi_id in current_session[repo]:
            if fi_id in old_session[repo]:
                if old_session[repo][fi_id]['state'] != 'Finished':
                    updated_session[repo][fi_id] = current_session[repo][fi_id]
            else:
                if override_prompt(override):
                    return current_session
    return updated_session


def config_errors(message, default):
    """
    Handler that suppresses errors in config.yaml parsing if default config.yaml file has been provided.  Used to allow
    running without config.yaml file.
    :param message:
    :param default:
    :return:
    """
    if default:
        return {}
    else:
        print message
        raise click.Abort()


def config_parse(filename, default_filename, docker=False, docker_paths=None, empty_ok=False):
    """
    Parses config.yaml file.  If docker is enabled, will add default docker paths to configuration.
    :param filename:
    :param default_filename:
    :param docker:
    :param docker_paths:
    :param empty_ok:
    :return:
    """
    default = filename == default_filename
    try:
        config_file = open(filename, 'r')
    except IOError as ex:
        config_errors('Config file "{0}" not found: {1}'.format(filename, ex.strerror), default)
        if docker:
            return {'download': docker_paths, 'report': docker_paths, 'version': docker_paths, 'check': docker_paths}
        else:
            return {}
    try:
        yaml.SafeLoader.add_constructor('tag:yaml.org,2002:python/unicode', constructor)
        config_temp = yaml.safe_load(config_file)
        if config_temp:
            config = flatten_dict(normalize_keys(config_temp))
            if (docker or ('docker' in config and config['docker'])) and docker_paths:
                config.update(docker_paths)
            config = {'download': config, 'report': config, 'version': config, 'check': config}
            if 'logfile' in config_temp:
                config['logfile'] = config_temp['logfile']
            if 'docker' in config_temp:
                config['docker'] = config_temp['docker']
        elif empty_ok:
            return {}
        else:
            config = config_errors('Config file "{}" is an empty file.'.format(filename), default)
    except yaml.YAMLError:
        config = config_errors('Failed to parse config.yaml file "{}". Config must be in YAML format.'.format(filename),
                               default)
    return config


def constructor(node):
    """
    Yaml constructor used to load config.yaml file
    :param node:
    :return:
    """
    return node.value


def filter_manifest_ids(self, manifest_json, repos):
    """
    Function to return a list of unique file ids from a manifest.  Throws error if not unique, or no files found
    :param self:
    :param manifest_json:
    :param repos:
    :return:
    """
    fi_ids = []
    for repo_info in manifest_json['entries']:
        if repo_info['repo'] in repos:
            for file_info in repo_info['files']:
                if file_info['id'] in fi_ids:
                    self.logger.error('Supplied manifest has repeated file identifiers.  Please specify a ' +
                                      'list of repositories to prioritize')
                    raise click.Abort
                else:
                    fi_ids.append(file_info['id'])
    if not fi_ids:
        msg = 'Files specified are not found on configured repositories: ({})'.format(str.join(' ', repos))
        self.logger.warning(click.style(msg, fg='red', bold=True))
        help_msg = 'You can use the configure command to add any ' + \
                   'missing repositories or pass them in with the "-r" option.'
        self.logger.warning(click.style(help_msg, fg='red'))
        raise click.Abort
    return fi_ids


def filter_repos(repos):
    """
    Function to strip out null values from a list of repositories.  Throws error if all values are null.  Nulls are
    a common product of improper config.yaml file editing.
    :param repos:
    :return:
    """
    if not repos or repos.count(None) == len(repos):
        raise click.BadOptionUsage('Must include prioritized repositories')
    new_repos = []
    for repo in repos:
        if repo:
            new_repos.append(repo)
    return new_repos


def get_manifest_json(self, file_ids, api_url, repos, portal):
    """
    Wrapper around portal.get_manifest_id that handles errors and validates that only one manifest can be retrieved.
    :param self:
    :param file_ids:
    :param api_url:
    :param repos:
    :param portal:
    :return:
    """
    if len(file_ids) > 1:
        self.logger.error('For download from manifest files, multiple manifest id arguments is not supported')
        raise click.BadArgumentUsage('Multiple manifest files specified.')
    manifest_json = api_error_catch(self, portal.get_manifest_id, file_ids[0], api_url, repos)
    return manifest_json


def load_json(json_path, abort=True):
    """
    Function that reads state.json, attempts to kill all processes listed in state file,
     and removes json file if it is unreadable.
    :param json_path:
    :param abort:
    :return:
    """
    logger = logging.getLogger('__log__')
    if os.path.isfile(json_path):
        try:
            old_download_session = json.load(open(json_path, 'r+'))
            if abort and psutil.pid_exists(old_download_session['pid']):
                logger.error('Download currently in progress')
                raise click.Abort()
            for pid in old_download_session['subprocess']:
                if psutil.pid_exists(pid) and abort:
                    os.kill(pid, signal.SIGKILL)
                    try:
                        os.kill(pid, 0)
                        print 'Unable to kill client process with pid {}'.format(pid)
                    except OSError as ex:
                        if ex.errno == 3:
                            old_download_session['subprocess'].remove(pid)
                            continue
                        else:
                            logger.warning(ex.message)
            return old_download_session
        except ValueError:
            logger.info('Corrupted download state found.  Cleaning...')
            os.remove(json_path)
    return None


def match_repositories(self, repos, copies):
    """
    Function that finds the fileCopy object that corresponds to the highest priority repository for one file
    :param self:
    :param repos:
    :param copies:
    :return:
    """
    for repository in repos:
        for copy in copies['fileCopies']:
            if repository == copy['repoCode']:
                return repository, copy
    self.logger.error('File {0} not found on repositories: {1}'.format(copies['id'], ' '.join(repos)))
    return None, None


def override_prompt(override):
    """
    Overridable prompt that warns the user if state file doesn't match current command.
    :param override:
    :return:
    """
    if override:
        return True
    if click.confirm('Previous session data does not match current command.  Ok to overwrite previous session info?'):
        return True
    else:
        raise click.Abort


def validate_ids(ids, manifest):
    """
    Function to ensure formatting of supplied FI ids and uuids is correct.
    :param ids:
    :param manifest:
    :return:
    """
    if manifest:
        if not re.match(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', ids[0]):
            raise click.BadArgumentUsage(message='Bad Manifest ID: passed argument' +
                                                 '"{}" is not in uuid format'.format(ids[0]))
    else:
        for fi_id in ids:
            if not re.findall(r'FI\d*', fi_id):
                if re.match(r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}', fi_id):
                    raise click.BadArgumentUsage(message='Bad FI ID: passed argument "{}"'.format(fi_id) +
                                                 'is in UUID format.  If you intended to use a manifest,' +
                                                 'add the -m tag.')
                raise click.BadArgumentUsage(message='Bad FI ID: passed argument "{}"'.format(fi_id) +
                                             ' is not in FI00000 format')
