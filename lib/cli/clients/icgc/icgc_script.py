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


def icgc_call(object_id, token, tool_path, file_from, output, repo):

    os.environ['ACCESSTOKEN'] = token
    if file_from is not None:  # transport.file.from.icgc defaults to none, triggering memory mapped download
        os.environ['TRANSPORT_FILEFROM'] = file_from
    call_args = [tool_path, 'download', '--object-id', ''.join(object_id), '--output-dir', output]
    # object id is passed as a single element list to support multiple id's on other clients.
    run_command(call_args)


def icgc_manifest_call(manifest, token, tool_path, file_from, output, repo):

    os.environ['ACCESSTOKEN'] = token

    if file_from is not None:
        os.environ['TRANSPORT_FILEFROM'] = file_from
    call_args = [tool_path, 'download', '--manifest', manifest,  '--output-dir', output]
    run_command(call_args)
