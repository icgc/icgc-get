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
import os
import shutil
from icgcget.clients.download_client import DownloadClient
from icgcget.clients.errors import SubprocessError


class GnosDownloadClient(DownloadClient):

    def __init__(self, json_path=None, docker=False, log_dir=None, container_version=''):
        super(GnosDownloadClient, self).__init__(json_path, docker, log_dir, container_version=container_version)
        self.repo = 'cghub'
        self.log_name = '/gnos_log.log'

    def download(self, uuids, access, tool_path, staging, processes, udt=None, file_from=None, repo=None,
                 password=None):
        access_file = self.get_access_file(access, staging)
        call_args = self.make_call_args(tool_path, staging, access_file, uuids)
        code = self._run_command(call_args, self.download_parser)
        if self.docker:
            shutil.move(staging + self.log_name, self.log_dir + self.log_name)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None):
        access_file = self.get_access_file(access, output)
        call_args = self.make_call_args(path, output, access_file, uuids)
        result = self._run_test_command(call_args, "403 Forbidden", "404 Not Found")
        if self.docker:
            shutil.move(output + '/gnos_log', self.log_dir + '/gnos_log')
        if result == 0:
            return True
        elif result == 3:
            return False
        elif result == 2:
            raise SubprocessError(result, "Path to gentorrent client did not lead to expected application")
        else:
            raise SubprocessError(result, "Genetorrent failed with code {}".format(result))

    def print_version(self, path):
        super(GnosDownloadClient, self).print_version(path)

    def version_parser(self, response):
        version = re.findall(r"release [0-9.]+", response)
        if version:
            version = version[0][8:]
            self.logger.info(" Gtdownload Version:          %s", version)

    def download_parser(self, response):
        self.logger.info(response.strip())
        filename = re.findall(r'filename=*', response)
        if filename:
            filename = filename[9:]
            self.session_update(filename, 'cghub')

    def make_call_args(self, tool_path, staging, access_file, uuids):
        log_name = '/gnos_log.log'
        logfile = self.log_dir + log_name
        if self.docker:
            access_path = self.docker_mnt + '/' + os.path.basename(access_file.name)
            # Client needs to be run using sh to be able to download files in docker container.
            call_args = ['/bin/sh', '-c', tool_path + ' -vv' + ' -d ' + ' '.join(uuids) + ' -c ' + access_path +
                         ' -p ' + self.docker_mnt + ' -l ' + self.docker_mnt + log_name]
            call_args = self.prepend_docker_args(call_args, staging)
        else:
            call_args = [tool_path, '-vv', '-d']
            call_args.extend(uuids)
            call_args.extend(['-c', access_file.name, '-p', staging, '-l', logfile])
        return call_args
