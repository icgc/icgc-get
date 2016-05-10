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

from ..run_command import run_command
import tempfile


def icgc_call(object_id, token, tool_path, file_from, parallel, output, repo):
    env = dict(os.environ, ACCESSTOKEN=token, TRANSPORT_PARALLEL=parallel, TRANSPORT_FILEFROM=file_from)
    call_args = [tool_path, '--profile',  repo,  'download', '--object-id']
    call_args.extend(object_id)
    call_args.extend(['--output-dir', output])
    # object id is passed as a single element list to support multiple id's on other clients.
    code = run_command(call_args, env)
    return code


def icgc_manifest_call(manifest, token, tool_path, file_from, parallel, output, repo):
    os.environ['ACCESSTOKEN'] = token
    os.environ['TRANSPORT_PARALLEL'] = parallel
    if file_from is not None:
        os.environ['TRANSPORT_FILEFROM'] = file_from
    t = tempfile.NamedTemporaryFile()
    t.write(manifest)
    t.seek(0)
    call_args = [tool_path, '--profile', repo, 'download', '--manifest', t.name, '--output-dir', output]
    code = run_command(call_args)
    return code
