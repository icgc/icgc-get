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

import requests
import logging
from errors import ApiError


def call_api(request, api_url, headers=None, head=False):
    logger = logging.getLogger("__log__")
    try:
        if head:
            resp = requests.head(request, headers=headers)
        else:
            resp = requests.get(request, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logger.debug(e.message)
        raise ApiError(request, "Unable to connect to the icgc api at {}".format(api_url))
    except requests.exceptions.Timeout as e:
        logger.debug(e.message)
        raise ApiError(request, e.message)
    except requests.exceptions.RequestException as e:
        logger.error(e.message)
        raise ApiError(request, e.message)
    if resp.status_code != 200:
        raise ApiError(request, "API request failed due to {} error.".format(resp.reason, resp.text),
                       code=resp.status_code)
    return resp.json()


class IcgcPortalClient:
    def __init__(self):
        self.logger = logging.getLogger('__log__')

    def get_manifest_id(self, manifest_id, api_url, repos=None):
        fields = 'fields=id,size,content,repoFileId'
        if repos:
            request = (api_url + 'manifests/' + manifest_id + '?repos=' + ','.join(repos) +
                       '&unique=true&' + fields)
        else:
            request = api_url + 'manifests/' + manifest_id + '?' + fields
        try:
            entity_set = call_api(request, api_url)
        except ApiError as e:
            if e.code == 404:
                self.logger.error("Manifest {} not found in database. ".format(manifest_id) +
                                  " Please check your manifest id")
            raise ApiError(e.request_string, '', e.code)
        return entity_set

    def get_manifest(self, file_ids, api_url, repos=None):
        fields = '&fields=id,size,content,repoFileId'
        if repos:
            request = (api_url + 'manifests' + self.filters(file_ids) + '&repos=' + ','.join(repos) + '&unique=true&' +
                       fields)
        else:
            request = api_url + 'manifests' + self.filters(file_ids) + fields
        entity_set = call_api(request, api_url)
        return entity_set

    def get_metadata_bulk(self, file_ids, api_url):
        entity_set = []
        pages_available = True
        while pages_available:
            request = (api_url + 'repository/files' + self.filters(file_ids) +
                       '"&&from=1&size=10&sort=id&order=desc')
            resp = call_api(request, api_url)
            entity_set.extend(resp["hits"])
            pages = resp["pagination"]["pages"]
            page = resp["pagination"]["page"]
            pages_available = page < pages
        return entity_set

    @staticmethod
    def filters(file_ids):
        return '?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + '"]}}}'
