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
import tempfile
from icgcget.clients.errors import ApiError
from icgcget.clients.download_client import DownloadClient
from icgcget.clients.portal_client import call_api


class GdcDownloadClient(DownloadClient):

    def __init__(self, json_path=None, verify=True):
        super(GdcDownloadClient, self) .__init__(json_path)
        self.repo = 'gdc'
        self.verify = verify

    def download(self, uuids, access, tool_path, output, processes, udt=None, file_from=None, repo=None, password=None):
        call_args = [tool_path, 'download']
        call_args.extend(uuids)
        call_args.extend(['--dir', output, '-n', processes])

        if access is not None:  # Enables download of unsecured gdc data
            access_file = tempfile.NamedTemporaryFile()
            access_file.file.write(access)
            access_file.file.seek(0)
            call_args.extend(['--token', access_file.name])
        if udt:
            call_args.append('--udt')
        code = self._run_command(call_args, self.download_parser)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, password=None):
        base_url = 'https://gdc-api.nci.nih.gov/data/'
        request = base_url + ','.join(uuids)
        header = {'X-auth-Token': access}
        try:
            call_api(request, header, head=True, verify=self.verify)
            return True
        except ApiError as ex:
            if ex.code == 403:
                return False
            else:
                raise ex

    def print_version(self, path):
        self._run_command([path, '--version'], self.version_parser)

    def version_parser(self, response):
        version = re.findall(r"v[0-9.]+", response)
        if version:
            version = version[0][1:]
            self.logger.info(" GDC Client Version:          %s", version)

    def download_parser(self, response):
        file_id = re.findall(r'v------ \w{8}-\w{4}-\w{4}-\w{4}-\w{12} ------v', response)
        if file_id:
            file_id = file_id[8:-8]
            self.session_update(file_id, 'gdc')
        self.logger.info(response)
