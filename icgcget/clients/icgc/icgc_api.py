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


def call_api(request, api_url):
    logger = logging.getLogger("__log__")
    try:
        resp = requests.get(request, timeout=0.1)
    except requests.exceptions.ConnectionError as e:
        logger.info("Unable to connect to the icgc api at {}.".format(api_url))
        logger.debug(e.message)
        raise RuntimeError("Unable to connect to the icgc at {}.".format(api_url))
    except requests.exceptions.Timeout as e:
        logger.info("Error: Connection timed out")
        logger.debug(e.message)
        raise RuntimeError(e.message)
    except requests.exceptions.RequestException as e:
        logger.info(e.message)
        raise RuntimeError(e.message)
    if resp.status_code != 200:
        logger.debug(resp.raw)
        logger.info("API request {} failed with status code {}", request, resp.status_code)
        raise RuntimeError("API request {} failed with status code {}".format(request, resp.status_code))
    return resp


def get_metadata(file_id, api_url):

    request = api_url + "files/" + file_id
    resp = call_api(request, api_url)
    datafile = resp.json()
    return datafile


def read_manifest(manifest_id, api_url):
    request = api_url + 'manifests/' + manifest_id
    resp = call_api(request, api_url)
    entity_set = resp.json()
    return entity_set
