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
import abc
import logging
import json
import subprocess
import tempfile
import shutil
import os
import re
import subprocess32


class DownloadClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, json_path=None, docker=False, log_dir=None, container_version=""):

        self.logger = logging.getLogger('__log__')
        self.jobs = []
        self.session = {}
        self.log_dir = log_dir
        self.path = json_path
        self.docker = docker
        self.repo = ''
        self.docker_mnt = '/icgc/mnt'
        self.docker_version = 'icgc/icgc-get:' + container_version

    @abc.abstractmethod
    def download(self, manifest, access, tool_path, staging, processes, udt=None, file_from=None, repo=None,
                 password=None):
        return

    @abc.abstractmethod
    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None):
        return

    @abc.abstractmethod
    def print_version(self, path):
        call_args = [path, '--version']
        if self.docker:
            call_args = self.prepend_docker_args(call_args)
        self._run_command(call_args, self.version_parser)

    @abc.abstractmethod
    def version_parser(self, output):
        return

    @abc.abstractmethod
    def download_parser(self, output):
        self.logger.info(output)

    def _run_command(self, args, parser, env=None):
        self.logger.debug(args)
        if None in args:
            self.logger.warning("Missing argument in %s", args)
            return 1
        if not env:
            env = dict(os.environ)
        env['PATH'] = '/usr/local/bin:' + env['PATH']  # virtalenv compatibility
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as ex:
            self.logger.warning(ex.output)
            return ex.returncode
        except OSError:
            self.logger.warning("Path to download tool, %s, does not lead to expected application", args[0])
            return 2
        while True:
            output = process.stdout.readline()
            if process.poll() is not None:
                break
            if output:
                parser(output)
        return_code = process.poll()
        if return_code == 0 and self.session:
            self.session_update('', self.repo)  # clear any running files if exit cleanly
        return return_code

    def session_update(self, file_name, repo):
        for name, file_object in self.session['file_data'][repo].iteritems():
            if file_object['index_filename'] == file_name or file_object['fileName'] == file_name or \
                            file_object['fileUrl'] == file_name:
                file_object['state'] = 'Running'
                self.session['file_data'][repo][name] = file_object
            elif file_object['state'] == 'Running':  # only one file at a time can be downloaded.
                file_object['state'] = 'Finished'
                self.session['file_data'][repo][name] = file_object
        json.dump(self.session, open(self.path, 'w', 0777))

    def _run_test_command(self, args, forbidden, not_found, env=None, timeout=2):
        if not env:
            env = dict(os.environ)
        env['PATH'] = '/usr/local/bin:' + env['PATH']
        if None in args:
            self.logger.warning("Missing argument in %s", args)
            return 1
        try:
            subprocess32.check_output(args, stderr=subprocess.STDOUT, env=env, timeout=timeout)
        except subprocess32.CalledProcessError as ex:
            code = self.parse_test_ex(ex, forbidden, not_found)
            if code == 0:
                return ex.returncode
            else:
                return code
        except OSError:
            return 2
        except subprocess32.TimeoutExpired as ex:
            code = self.parse_test_ex(ex, forbidden, not_found)
            return code

    @staticmethod
    def parse_test_ex(ex, forbidden, not_found):
        invalid_login = re.findall(forbidden, ex.output)
        not_found = re.findall(not_found, ex.output)
        if invalid_login:
            return 3
        elif not_found:
            return 404
        else:
            return 0

    def prepend_docker_args(self, args, mnt=None, envvars=None):
        docker_args = ['docker', 'run', '-t', '--rm']
        if not envvars:
            envvars = {}
        for name, value in envvars.iteritems():
            docker_args.extend(['-e', name + '=' + value])
        if mnt:
            docker_args.extend(['-v', mnt + ':' + self.docker_mnt])
        docker_args.append(self.docker_version)
        return docker_args + args

    def get_access_file(self, access, staging):
        if os.path.isfile(access):
            if self.docker and os.path.split(access)[1] != staging:
                access_file = tempfile.NamedTemporaryFile(dir=staging)
                shutil.copyfile(access, access_file.name)
            else:
                access_file = open(access)
        else:
            access_file = tempfile.NamedTemporaryFile(dir=staging)
            access_file.file.write(access)
            access_file.file.seek(0)
        return access_file
