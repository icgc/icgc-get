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

from icgcget.clients.download_client import DownloadClient
from icgcget.clients.errors import SubprocessError


class GnosDownloadClient(DownloadClient):

    def __init__(self, pickle_path=None):
        super(GnosDownloadClient, self) .__init__(pickle_path)
        self.repo = 'cghub'

    def download(self, uuids, access, tool_path, output, processes, udt=None, file_from=None, repo=None, region=None):
        call_args = [tool_path, '-vv', '-c', access, '-d']
        call_args.extend(uuids)
        call_args.extend(['-p', output])
        code = self._run_command(call_args, self.download_parser)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, region=None):
        call_args = [path, '-vv', '-c', access, '-d']
        call_args.extend(uuids)
        call_args.extend(['-p', output])
        result = self._run_test_command(call_args)
        if result == 0:
            return True
        elif result == 3:
            return False
        elif result == 2:
            raise SubprocessError(result, "Path to gentorrent client did not lead to expected application")
        else:
            raise SubprocessError(result, "Genetorrent failed with code {}".format(result))

    def print_version(self, path, access=None):
        self._run_command([path, '--version'], self.version_parser)

    def version_parser(self, response):
        version = re.findall(r"elease [0-9.]+", response)
        if version:
            self.logger.info("Gtdownload R{}".format(version[0]))

    def download_parser(self, response):
        self.logger.info(response)
        filename = re.findall(r'filename=*', response)
        if filename:
            filename = filename[9:]
            self.session_update(filename, 'cghub')

