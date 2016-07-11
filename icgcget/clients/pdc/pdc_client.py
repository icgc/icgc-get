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
from icgcget.clients.errors import SubprocessError
from icgcget.clients.download_client import DownloadClient


class PdcDownloadClient(DownloadClient):

    def __init__(self, json_path=None, docker=False, log_dir=None, container_version=''):
        super(PdcDownloadClient, self).__init__(json_path, docker, log_dir, container_version=container_version)
        self.repo = 'pdc'
        self.url = '--endpoint-url=https://bionimbus-objstore.opensciencedatacloud.org/'

    def download(self, data_paths, key, tool_path, staging, processes, udt=None, file_from=None, repo=None,
                 secret_key=None):
        code = 0
        env_dict = dict(os.environ)

        for data_path in data_paths:
            call_args = [tool_path, '--debug' 's3', self.url, 'cp', data_path]
            if self.docker:
                call_args.extend([self.docker_mnt + '/'])
                envvars = {'AWS_ACCESS_KEY_ID': key, 'AWS_SECRET_ACCESS_KEY': secret_key}
                call_args = self.prepend_docker_args(call_args, staging, envvars)
            else:
                env_dict['AWS_ACCESS_KEY_ID'] = key
                env_dict['AWS_SECRET_ACCESS_KEY'] = secret_key
                call_args.extend([staging + '/'])
            code = self._run_command(call_args, self.download_parser, env=env_dict)
            if code != 0:
                return code
            self.session_update(data_path, 'pdc')
        return code

    def access_check(self, key, data_paths=None, path=None, repo=None, output=None, api_url=None, secret_key=None):
        env_dict = dict(os.environ)
        env_dict['AWS_ACCESS_KEY_ID'] = key
        env_dict['AWS_SECRET_ACCESS_KEY'] = secret_key
        for data_path in data_paths:

            call_args = [path, 's3', self.url, 'cp', data_path]
            if self.docker:
                call_args.append(self.docker_mnt + '/')
                envvars = {'AWS_ACCESS_KEY_ID': key, 'AWS_SECRET_ACCESS_KEY': secret_key}
                call_args = self.prepend_docker_args(call_args, output, envvars)
            else:
                call_args.append(output + '/')
            call_args.append('--dryrun')
            result = self._run_test_command(call_args, "(403)", "(404)", env_dict, timeout=4)
            if result == 3:
                return False
            elif result == 0:
                return True
            elif result == 2:
                raise SubprocessError(result, "Path to AWS client did not lead to expected application")
            else:
                raise SubprocessError(result, "AWS failed with code {}".format(result))

    def print_version(self, path):
        super(PdcDownloadClient, self).print_version(path)

    def download_parser(self, output):
        self.logger.info(output)

    def version_parser(self, output):
        version = re.findall(r"aws-cli/[0-9.]+", output)
        if version:
            self.logger.info(" AWS CLI Version:             %s", version[0][8:])
