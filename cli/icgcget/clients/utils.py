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

import collections
import yaml
import os


def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def convert_size(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G', 'T']:
        if abs(num) < 1024.0:
            return ["%3.2f" % num,  "%s%s" % (unit, suffix)]
        num /= 1024.0
    return ["%.2f" % num, "%s%s" % ('Yi', suffix)]


def get_api_url(context_map):
    if os.getenv("ICGCGET_API_URL"):
        api_url = os.getenv("ICGCGET_API_URL")
    else:
        api_url = context_map["portal_url"] + 'api/v1/'
    return api_url


def normalize_keys(obj):
    if type(obj) != dict:
        return obj
    else:
        return {k.replace('.', '_'): normalize_keys(v) for k, v in obj.items()}


def config_parse(filename):
    config = {}
    try:
        config_text = open(filename, 'r')
    except IOError:

        print("Config file {} not found".format(filename))
        return config
    try:
        config_temp = yaml.safe_load(config_text)
        config_download = flatten_dict(normalize_keys(config_temp))
        config = {'download': config_download, 'status': config_download, 'version': config_download,
                  'logfile': config_temp['logfile']}
    except yaml.YAMLError:

        print("Could not read config file {}".format(filename))
        return {}

    return config


def donor_addition(donor_list, donor):
    if donor not in donor_list:
        donor_list.append(donor)
    return donor_list


def increment_types(typename, repository, size_dict, count_dict, size):
    if typename not in size_dict[repository]:
        size_dict[repository][typename] = 0
    if typename not in count_dict:
        count_dict[repository][typename] = 0
    size_dict[repository]["total"] += size
    size_dict[repository][typename] += size
    count_dict[repository]["total"] += 1
    count_dict[repository][typename] += 1
    return size_dict, count_dict


def calculate_size(manifest_json):
    size = 0
    object_ids = {}
    for repo_info in manifest_json["entries"]:
        repo = repo_info["repo"]
        object_ids[repo] = {}
        for file_info in repo_info["files"]:
            object_ids[repo][file_info['id']] = {'uuid': file_info["repoFileId"], 'state': "Not started",
                                                 'filename': 'None', 'index_filename': 'None', 'fileUrl': 'None'}
            size += file_info["size"]
    return size, object_ids
