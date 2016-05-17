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
import tempfile

from ..portal_client import call_api
from ..download_client import DownloadClient
from ..icgcget_errors import ApiError
from ..run_command import run_command


class GdcDownloadClient(DownloadClient):

    def download(self, manifest, access, tool_path, output,  processes, udt=None, file_from=None, repo=None):
        t = tempfile.NamedTemporaryFile()
        t.write(manifest)
        t.seek(0)
        call_args = [tool_path, 'download', '-m', t.name, '--dir', output, '-n', processes]
        if access is not None:  # Enables download of unsecured gdc data
            call_args.extend(['-t', access])
        if udt:
            call_args.append('--udt')
        code = run_command(call_args)
        return code

    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None):
        base_url = 'https://gdc-api.nci.nih.gov/data/'
        request = base_url + ','.join(uuids)
        header = {'X-auth-Token': access}
        try:
            call_api(request, base_url, header, head=True)
            return True
        except ApiError as e:
            if e.code == 403:
                return False
            else:
                raise e
