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

import fnmatch
import os
import re
from random import SystemRandom
from string import ascii_uppercase, digits
from urllib import quote

from requests import HTTPError

from icgcget.clients.download_client import DownloadClient
from icgcget.clients.portal_client import call_api


class EgaDownloadClient(DownloadClient):

    def __init__(self, pickle_path=None):
        super(EgaDownloadClient, self) .__init__(pickle_path)
        self.repo = 'ega'

    def download(self, object_ids, access, tool_path, output, parallel, udt=None, file_from=None, repo=None,
                 region=None):

        key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))
        label = object_ids[0] + '_download_request'
        args = ['java', '-jar', tool_path, '-pf', access, '-nt', parallel]
        for object_id in object_ids:

            request_call_args = args
            if object_id[3] == 'D':
                request_call_args.append('-rfd')
            else:
                request_call_args.append('-rf')
            request_call_args.extend([object_id, '-re', key, '-label', label])
            rc_request = self._run_command(request_call_args, self.download_parser)
            if rc_request != 0:
                return rc_request
        download_call_args = args
        download_call_args.extend(['-dr', label, '-path', output])
        if udt:
            download_call_args.append('-udt')
        rc_download = self._run_command(download_call_args, self.download_parser)
        if rc_download != 0:
            return rc_download
        decrypt_call_args = args
        decrypt_call_args.append('-dc')
        for cip_file in os.listdir(output):  # File names cannot be dynamically predicted from dataset names
            if fnmatch.fnmatch(cip_file, '*.cip'):  # Tool attempts to decrypt all encrypted files in download directory
                decrypt_call_args.append(output + '/' + cip_file)

        decrypt_call_args.extend(['-dck', key])
        rc_decrypt = self._run_command(decrypt_call_args, self.download_parser)
        if rc_decrypt != 0:
            return rc_decrypt
        return 0

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, region=None):
        base_url = "https://ega.ebi.ac.uk/ega/rest/access/v2/"
        access_file = open(access)
        username = access_file.readline()
        password = access_file.readline()
        login_request = base_url + 'users/' + quote(username.rstrip()) + "?pass=" + quote(password.rstrip())
        try:
            resp = call_api(login_request, base_url)
        except HTTPError:  # invalid return code
            return False
        if resp["header"]["userMessage"] == "OK":
            session_id = resp["response"]["result"][1]
            dataset_request = base_url + "datasets?session=" + session_id
            try:
                dataset_response = call_api(dataset_request, base_url)
                data_sets = dataset_response["response"]["result"]
            except HTTPError:
                return False
            if "EGAD00001000023" in data_sets and "EGAD00010000562" in data_sets:
                return True

        return False

    def print_version(self, path, access=None):
        self._run_command(['java', '-jar', path, '-pf', access], self.version_parser)

    def version_parser(self, response):
        version = re.findall(r"Version: [0-9.]+", response)
        if version:
            self.logger.info("EGA Client {}".format(version[0]))

    def download_parser(self, response):
        filename = re.findall(r'/[^/]+.cip  \(', response)
        if filename:
            filename = filename[0][1:-7]
            self.session_update(filename, 'ega')
        self.logger.info(response)
