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

from ..run_command import run_command


def gdc_call(uuid, token, tool_path, output, udt, processes):
    call_args = [tool_path, 'download']
    call_args.extend(uuid)
    if token is not None:  # Enables download of unsecured gdc-data
        call_args.extend(['-t', token])
    call_args.extend(['--dir', output, '-n', processes])
    if udt:
        call_args.append('--udt')
    code = run_command(call_args)
    return code


def gdc_manifest_call(manifest, token, tool_path, output, udt, processes):
    call_args = [tool_path, 'download', '-m', manifest, '--dir', output, '-n', processes]
    if token is not None:  # Enables download of unsecured gdc data
        call_args.extend(['-t', token])
    if udt:
        call_args.append('--udt')
    code = run_command(call_args)
    return code
