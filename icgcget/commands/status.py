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

import logging
import pickle
from icgcget.clients.utils import convert_size


def check_download(pickle_path):
    logger = logging.getLogger('__log__')
    status = pickle.load(open(pickle_path, 'r+'))
    for repo in status:
        finished = 0
        not_started = 0
        for fi_id in status[repo]:
            if status[repo][fi_id]['state'] == 'finished':
                finished += status[repo][fi_id]['size']
            elif status[repo][fi_id]['state'] == 'not_started':
                not_started += status[repo][fi_id]['size']
        finished_size = convert_size(finished)
        finished_size = finished_size[0] + finished_size[1]
        not_started_size = convert_size(not_started)
        not_started_size = not_started_size[0] + not_started_size[1]
        logger.warning('{0} files to download, {1} files downloaded from {2}'.format(finished, not_started, repo))
        logger.warning('{0} to download, {1} downloaded from {2}'.format(finished_size, not_started_size, repo))
