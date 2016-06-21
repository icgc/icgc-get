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
import logging
import os
import shutil
import datetime

import click
import psutil
from icgcget.clients import portal_client
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.clients.utils import calculate_size, convert_size, search_recursive

from icgcget.commands.utils import api_error_catch, filter_manifest_ids, check_access, get_manifest_json


class DownloadDispatcher(object):
    def __init__(self, pickle_path):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient(pickle_path)
        self.ega_client = EgaDownloadClient(pickle_path)
        self.gt_client = GnosDownloadClient(pickle_path)
        self.pdc_client = PdcDownloadClient(pickle_path)
        self.icgc_client = StorageClient(pickle_path)

    def download_manifest(self, repos, file_ids, manifest, output, api_url, verify):
        portal = portal_client.IcgcPortalClient(verify)
        manifest_json = self.get_manifest(manifest, file_ids, api_url, repos, portal)
        session_info = {'pid': os.getpid(), 'start_time': datetime.datetime.utcnow().isoformat(), 'command': file_ids}
        size = calculate_size(manifest_json, session_info)
        object_ids = session_info['object_ids']
        if manifest:
            file_ids = []
            for repo in object_ids:
                file_ids.extend(object_ids[repo].keys())

        entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
        for entity in entities:
            for repo_id in object_ids:
                if entity['id'] in object_ids[repo_id]:
                    repo = repo_id
                    break
            else:
                self.logger.warning("File %s not found on any of the specified repositories", entity["id"])
                continue

            file_copies = entity['fileCopies']
            for copy in file_copies:
                if copy['repoCode'] == repo:
                    if search_recursive(copy["fileName"], output):
                        object_ids[repo].pop(entity['id'])
                        self.logger.warning("File %s found in download directory, skipping", entity['id'])
                        break
                    object_ids[repo][entity["id"]]['filename'] = copy["fileName"]
                    if "fileName" in copy["indexFile"]:
                        object_ids[repo][entity["id"]]['index_filename'] = copy["indexFile"]["fileName"]
                    if repo == 'pdc':
                        object_ids[repo][entity['id']]['fileUrl'] = 's3://' + copy['repoDataPath']
                        if output and copy['repoDataPath'].split('/')[1] in os.listdir(output):
                            object_ids[repo].pop(entity['id'])
                            self.logger.warning("File %s found in download directory, skipping", entity['id'])
                            break
        self.size_check(size, output)
        session_info['object_ids'] = object_ids
        return session_info

    def download(self, session, staging, output,
                 cghub_key, cghub_path, cghub_transport_parallel,
                 ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                 gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                 pdc_key, pdc_secret_key, pdc_path, pdc_transport_parallel):
        object_ids = session['object_ids']
        if 'cghub' in object_ids and object_ids['cghub']:
            check_access(self, cghub_key, 'cghub', cghub_path)
            self.gt_client.session = session
            uuids = self.get_uuids(object_ids['cghub'])
            return_code = self.gt_client.download(uuids, cghub_key, cghub_path, staging, cghub_transport_parallel)
            object_ids = self.icgc_client.session
            self.check_code('Cghub', return_code)
            self.move_files(staging, output)

        if 'aws-virginia' in object_ids and object_ids['aws-virginia']:
            check_access(self, icgc_token, 'icgc', icgc_path)
            self.icgc_client.session = session
            uuids = self.get_uuids(object_ids['aws-virginia'])
            return_code = self.icgc_client.download(uuids, icgc_token, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='aws')
            object_ids = self.icgc_client.session
            self.check_code('Icgc', return_code)
            self.move_files(staging, output)

        if 'ega' in object_ids and object_ids['ega']:
            check_access(self, ega_username, 'ega', ega_path, ega_password, udt=ega_udt)
            if ega_transport_parallel != '1':
                self.logger.warning("Parallel streams on the ega client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            self.ega_client.session = session
            uuids = self.get_uuids(object_ids['ega'])
            return_code = self.ega_client.download(uuids, ega_username, ega_path, staging, ega_transport_parallel,
                                                   ega_udt, password=ega_password)
            object_ids = self.icgc_client.session
            self.check_code('Ega', return_code)
            self.move_files(staging, output)

        if 'collaboratory' in object_ids and object_ids['collaboratory']:
            check_access(self, icgc_token, 'icgc', icgc_path)
            self.icgc_client.session = session
            uuids = self.get_uuids(object_ids['collaboratory'])
            return_code = self.icgc_client.download(uuids, icgc_token, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='collab')
            object_ids = self.icgc_client.session
            self.check_code('Icgc', return_code)
            self.move_files(staging, output)

        if 'pdc' in object_ids and object_ids['pdc']:
            check_access(self, pdc_key, 'pdc', pdc_path, secret_key=pdc_secret_key)
            urls = []
            for object_id in object_ids['pdc']:
                urls.append(object_ids['pdc'][object_id]['fileUrl'])
            self.pdc_client.session = session
            return_code = self.pdc_client.download(urls, pdc_key, pdc_path, staging, pdc_transport_parallel,
                                                   secret_key=pdc_secret_key)
            self.check_code('Aws', return_code)
            self.move_files(staging, output)

        if 'gdc' in object_ids and object_ids['gdc']:
            check_access(self, gdc_token, 'gdc', gdc_path, udt=gdc_udt)
            uuids = self.get_uuids(object_ids['gdc'])
            self.gdc_client.session = session
            return_code = self.gdc_client.download(uuids, gdc_token, gdc_path, staging, gdc_transport_parallel,
                                                   gdc_udt)
            self.check_code('Gdc', return_code)
        self.move_files(staging, output)

    def check_code(self, client, code):
        if code != 0:
            self.logger.error("%s client exited with a nonzero error code %s.", client, code)
            raise click.ClickException("Please check client output for error messages")

    def size_check(self, size, output):
        if output:
            free = psutil.disk_usage(output)[2]
            if free <= size:
                self.logger.error("Not enough space detected for download of %s. %s of space in %s",
                                  ''.join(convert_size(size)), ''.join(convert_size(free)), output)

    @staticmethod
    def get_uuids(object_ids):
        uuids = []
        for object_id in object_ids:
            uuids.append(object_ids[object_id]['uuid'])
        return uuids

    def get_manifest(self, manifest, file_ids, api_url, repos, portal):
        if manifest:
            manifest_json = get_manifest_json(self, file_ids, api_url, repos, portal)
        else:
            manifest_json = api_error_catch(self, portal.get_manifest, file_ids, api_url, repos)

        if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
            filter_manifest_ids(self, manifest_json, repos)
        return manifest_json

    def move_files(self, staging, output):
        for root, dirs, files in os.walk(staging, topdown=False):
            for staged_file in files:
                if staged_file != "state.json":
                    try:
                        shutil.move(os.path.join(root, staged_file), output)
                    except shutil.Error:
                        self.logger.warning('File %s already present in download directory', staged_file)
                        os.remove(os.path.join(root, staged_file))
            for stage_dir in dirs:
                os.rmdir(os.path.join(root, stage_dir))
