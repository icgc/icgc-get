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

import os
import re
import shutil
import fileinput
from icgcget.clients.utils import client_style
from icgcget.clients.download_client import DownloadClient
from icgcget.clients.portal_client import call_api
from icgcget.clients.errors import ApiError


class StorageClient(DownloadClient):
    """
    Download client subclass for controlling downloads from the icgc storage client
    """

    def __init__(self, json_path=None, docker=False, verify=True, log_dir=None, container_version=''):
        super(StorageClient, self).__init__(json_path, log_dir, docker, container_version=container_version)
        self.verify = verify

    def download(self, uuids, access, tool_path, staging, processes, udt=None, file_from=None, repo=None,
                 password=None, secret_key=None):
        """
        Function that constructs arguments to make storage client download call
        :param uuids:
        :param access:
        :param tool_path:
        :param staging:
        :param processes:
        :param udt:
        :param file_from:
        :param repo:
        :param password:
        :param secret_key:
        :return:
        """

        env_dict = dict(os.environ)
        log_file = ''
        client_log_file_name = 'icgc-storage-client.log'
        if self.log_dir:
            log_file = self.log_dir + '/' + client_log_file_name
        log_staging = staging + '/' + client_log_file_name

        if file_from is not None:
            os.environ['TRANSPORT_FILEFROM'] = file_from
        call_args = [tool_path, '--profile', repo, 'download', '--object-id']
        call_args.extend(uuids)
        if repo == 'collab':
            self.repo = 'collaboratory'
        elif repo == 'aws':
            self.repo = 'aws-virginia'
        if self.docker:
            call_args.extend(['--output-dir', self.docker_mnt])
            envvars = {'ACCESSTOKEN': access, 'TRANSPORT_PARALLEL': processes}
            call_args = self.prepend_docker_args(call_args, staging, envvars)
        else:
            if self.log_dir:
                log_conf_path = os.path.abspath(os.path.join(os.path.dirname(tool_path), '../conf/logback.xml'))
                self.edit_logback(log_conf_path, log_file)
            env_dict['ACCESSTOKEN'] = access
            env_dict['TRANSPORT_PARALLEL'] = processes

            call_args.extend(['--output-dir', staging])
        code = self._run_command(call_args, parser=self.download_parser, env=env_dict)
        if self.docker and os.path.isfile(log_staging) and self.log_dir:
            shutil.move(log_staging, log_file)
        elif self.docker and os.path.isfile(log_staging):
            os.remove(log_staging)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None,
                     secret_key=None):
        """
        Function that calls the icgc api to determine the access of a given access token
        :param access:
        :param uuids:
        :param path:
        :param repo:
        :param output:
        :param api_url:
        :param password:
        :param secret_key:
        :return:
        """
        request = api_url + 'settings/tokens/' + access
        try:
            resp = call_api(request, verify=self.verify)
        except ApiError as ex:
            if ex.code == 400:
                return False
            raise ApiError(ex.request_string, ex.message, ex.code)
        match = repo + '.download'
        return match in resp['scope']

    def print_version(self, path):
        """
        Method to construct arguments and call subprocess to print version of storage client
        :param path:
        :return:
        """
        call_args = [path, 'version']
        if self.docker:
            call_args = self.prepend_docker_args(call_args)
        self._run_command(call_args, self.version_parser)

    def version_parser(self, response):
        """
        Method to parse version number from client version output
        :param response:
        :return:
        """
        response = re.sub(r"\x1b[^m]*m", '', response)  # Strip ANSI colour codes
        version = re.findall(r'Version: [0-9.]+', response)
        if version:
            self.logger.info(' ICGC Storage Client %s', version[0])

    def download_parser(self, response):
        """
        Method to parse and output client download response, tracking the current file that is being downloaded
        :param response:
        :return:
        """
        response = re.sub(r'\x1b[^m]*m', '', response)
        filename = re.findall(r'\(\w{8}-\w{4}-\w{4}-\w{4}-\w{12}.+', response)
        if filename:
            filename = filename[0][1:-1]
            self.session_update(filename, self.repo)
        self.logger.info(client_style(response.strip()))

    @staticmethod
    def edit_logback(logback, log_file):
        """
        Method to edit storage client's logging configuration file to place client logfile in desired location
        :param logback:
        :param log_file:
        :return:
        """
        for line in fileinput.input(logback, inplace=1):
            match = re.search(r'name="LOG_FILE"', line)
            if match:
                print '     <property name="LOG_FILE" value="%s"/>' % log_file
            else:
                print line.strip()
