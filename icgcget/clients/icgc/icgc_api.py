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


def call_api(request, api_url, headers=None, head=False):
    logger = logging.getLogger("__log__")
    try:
        if head:
            resp = requests.head(request, headers=headers)
        else:
            resp = requests.get(request, headers=headers)
    except requests.exceptions.ConnectionError as e:
        logger.info("Unable to connect to the icgc api at {}.".format(api_url))
        logger.debug(e.message)
        raise RuntimeError("Unable to connect to the icgc api at {}".format(api_url))
    except requests.exceptions.Timeout as e:
        logger.info("Error: Connection timed out")
        logger.debug(e.message)
        raise RuntimeError(e.message)
    except requests.exceptions.RequestException as e:
        logger.info(e.message)
        raise RuntimeError(e.message)
    if resp.status_code != 200:
        logger.warning("API request failed due to {} error.\n  {} ".format(resp.reason, resp.text))
        raise requests.HTTPError(resp.status_code)
    return resp.json()


def get_manifest_id(manifest_id, api_url, repos=None):

    if repos:
        request = api_url + 'manifests/' + manifest_id + '?repos=' + ','.join(repos) + \
                  '&unique=true&fields=id,size,content,repoFileId'
    else:
        request = api_url + 'manifests/' + manifest_id + '?fields=id,size,content,repoFileId'
    entity_set = call_api(request, api_url)
    return entity_set


def get_manifest(file_ids, api_url, repos=None):

    if repos:
        request = api_url + 'manifests?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + \
                            '"]}}}&repos=' + ','.join(repos) + '&unique=true&fields=id,size,content,repoFileId'
    else:
        request = api_url + 'manifests?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + \
                            '"]}}}&fields=id,size,content,repoFileId'
    entity_set = call_api(request, api_url)
    return entity_set


def get_metadata_bulk(file_ids, api_url):

    entity_set = []
    request = api_url + 'repository/files?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + \
                        '"]}}}&&from=1&size=10&sort=id&order=desc'
    resp = call_api(request, api_url)
    entity_set.extend(resp["hits"])
    pages = resp["pagination"]["pages"]
    page = 1
    while page < pages:
        request = api_url + 'files?filters={"file":{"id":{"is":["' + '","'.join(file_ids) + \
                  '"]}}}&&from={}&size=10&sort=id&order=desc'.format(page*10 + 1)
        resp = call_api(request, api_url)
        entity_set.append(resp["hits"])
        page = resp["pagination"]["pages"]
    return entity_set
