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
import requests
from icgcget.clients.errors import ApiError


def call_api(request, headers=None, head=False, verify=True):
    logger = logging.getLogger("__log__")
    try:
        if head:
            resp = requests.head(request, headers=headers, verify=verify)
        else:
            resp = requests.get(request, headers=headers, verify=verify)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout,
            requests.exceptions.RequestException) as ex:
        logger.debug(ex.message)
        raise ApiError(request, ex.message.message)
    if resp.status_code != 200:
        raise ApiError(request, "API request failed due to {} error.".format(resp.reason),
                       code=resp.status_code)
    return resp.json()


class IcgcPortalClient(object):
    def __init__(self, verify):
        self.logger = logging.getLogger('__log__')
        self.verify = verify

    def get_manifest_id(self, manifest_id, api_url, repos=None):
        fields = '&fields=id,size,content,repoFileId&format=json'
        if repos:
            request = (api_url + 'manifests/' + manifest_id + '?repos=' + ','.join(repos) +
                       '&unique=true&' + fields)
        else:
            request = api_url + 'manifests/' + manifest_id + '?' + fields
        try:
            entity_set = call_api(request, verify=self.verify)
        except ApiError as ex:
            if ex.code == 404:
                self.logger.error("Manifest {} not found on server. ".format(manifest_id) +
                                  " Please check your manifest id")
            raise ApiError(ex.request_string, ex.message, ex.code)
        return entity_set

    def get_manifest(self, file_ids, api_url, repos=None):
        fields = '&fields=id,size,content,repoFileId&format=json'
        if repos:
            request = (api_url + 'manifests' + self.filters(file_ids) + '&repos=' + ','.join(repos) + '&unique=true&' +
                       fields)
        else:
            request = api_url + 'manifests' + self.filters(file_ids) + fields
        entity_set = call_api(request, verify=self.verify)
        return entity_set

    def get_metadata_bulk(self, file_ids, api_url):
        entity_set = []
        pages_available = True
        while pages_available:
            request = (api_url + 'repository/files' + self.filters(file_ids) +
                       '"&&from=1&size=10&sort=id&order=desc')
            resp = call_api(request, verify=self.verify)
            entity_set.extend(resp["hits"])
            pages = resp["pagination"]["pages"]
            page = resp["pagination"]["page"]
            pages_available = page < pages
        return entity_set

    @staticmethod
    def filters(file_ids):
        return '?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + '"]}}}'
