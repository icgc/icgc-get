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
from random import SystemRandom
from string import ascii_uppercase, digits

from ..run_command import run_command


def ega_call(object_id, username, password, tool_path, parallel, udt, download_dir):
    object_id = ''.join(object_id)  # object id is  a single element list to support multiple id's on other clients
    label = object_id + '_request'
    key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))  # Make randomized decryption key
    args = ['java', '-jar', tool_path, '-p', username, password, '-nt', parallel]
    # Parameters needed for all ega client commands

    request_call_args = args
    if object_id[3] == 'D':
        request_call_args.append('-rfd')
    else:
        request_call_args.append('-rf')
    request_call_args.extend([object_id, '-re', key, '-label', label])
    rc_request = run_command(request_call_args)
    if rc_request != 0:
        return rc_request
    download_call_args = args
    download_call_args.extend(['-dr', label, '-path', download_dir])
    if udt:
        download_call_args.append('-udt')
    rc_download = run_command(download_call_args)
    if rc_download != 0:
        return rc_download
    decrypt_call_args = args
    decrypt_call_args.append('-dc')
    for file in os.listdir(download_dir):  # File names cannot be dynamically predicted from dataset names
        if fnmatch.fnmatch(file, '*.cip'):  # Tool attempts to decrypt all encrypted files in download directory.
            decrypt_call_args.append(download_dir + '/' + file)

    decrypt_call_args.extend(['-dck', key])
    rc_decrypt = run_command(decrypt_call_args)
    if rc_decrypt != 0:
        return rc_decrypt
    return 0
