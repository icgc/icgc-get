#!/usr/bin/python
# -*- coding: utf-8 -*-
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
from icgcget.clients.utils import calculate_size, convert_size, search_recursive, flatten_file_data


from icgcget.commands.utils import api_error_catch, filter_manifest_ids, check_access, get_manifest_json, \
    match_repositories


class DownloadDispatcher(object):
    def __init__(self, json_path=None, docker=False, logfile=None, container_version=''):
        log_dir = os.path.split(logfile)[0] if logfile else None
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient(json_path, docker, log_dir=log_dir, container_version=container_version)
        self.ega_client = EgaDownloadClient(json_path, docker, log_dir, container_version=container_version)
        self.gt_client = GnosDownloadClient(json_path, docker, log_dir, container_version=container_version)
        self.pdc_client = PdcDownloadClient(json_path, docker, log_dir, container_version=container_version)
        self.icgc_client = StorageClient(json_path, docker, log_dir=log_dir, container_version=container_version)

    def download_manifest(self, repos, file_ids, manifest, output, api_url, verify, unique=False):
        portal = portal_client.IcgcPortalClient(verify)
        manifest_json = self.get_manifest(manifest, file_ids, api_url, repos, portal)
        download_session = {'pid': os.getpid(), 'start_time': datetime.datetime.utcnow().isoformat(),
                            'command': file_ids}
        size, download_session = calculate_size(manifest_json, download_session)
        file_data = download_session['file_data']
        if manifest:
            file_ids = []
            for repo in file_data:
                file_ids.extend(file_data[repo].keys())
                self.logger.debug(file_data[repo].keys() + ' found on manifest')
        entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
        for entity in entities:
            repo, copy = match_repositories(self, repos, entity)
            if not repo:
                raise click.Abort()

            if copy['repoCode'] == repo:
                if unique and search_recursive(copy["fileName"], output):
                    file_data[repo].pop(entity['id'])
                    self.logger.warning("File %s found in download directory, skipping", entity['id'])
                    continue
                temp_file = {'fileName': copy["fileName"], 'dataType': entity["dataCategorization"]["dataType"],
                             'donors': entity["donors"], 'fileFormat': copy['fileFormat']}

                if "fileName" in copy["indexFile"]:
                    temp_file['index_filename'] = copy["indexFile"]["fileName"]
                if repo == 'pdc':
                    file_data[repo][entity['id']]['fileUrl'] = 's3://' + copy['repoDataPath']
                    if unique and search_recursive(copy['repoDataPath'].split('/')[1], output):
                        file_data[repo].pop(entity['id'])
                        self.logger.warning("File %s found in download directory, skipping", entity['id'])
                        continue
                file_data[repo][entity["id"]].update(temp_file)
                self.logger.debug('File %s added to file data under repo %s', entity['id'], repo)
        self.size_check(size, output)
        if not flatten_file_data(file_data):
            self.logger.error("All files were found in download directory, aborting")
            raise click.Abort
        download_session['file_data'] = file_data
        return download_session

    def download(self, session, staging, output,
                 cghub_key, cghub_path, cghub_transport_parallel,
                 ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                 gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                 pdc_key, pdc_secret_key, pdc_path, pdc_transport_parallel):
        file_data = session['file_data']

        if 'cghub' in file_data and file_data['cghub']:
            check_access(self, cghub_key, 'cghub', self.gt_client.docker, cghub_path)
            self.gt_client.session = session
            uuids = self.get_uuids(file_data['cghub'])
            return_code = self.gt_client.download(uuids, cghub_key, cghub_path, staging, cghub_transport_parallel)
            session = self.cleanup('CGHub', return_code, staging, output, self.gt_client)

        if 'aws-virginia' in file_data and file_data['aws-virginia']:
            check_access(self, icgc_token, 'icgc', self.icgc_client.docker, icgc_path)
            self.icgc_client.session = session
            uuids = self.get_uuids(file_data['aws-virginia'])
            return_code = self.icgc_client.download(uuids, icgc_token, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='aws')
            session = self.cleanup('ICGC', return_code, staging, output, self.icgc_client)

        if 'ega' in file_data and file_data['ega']:
            check_access(self, ega_username, 'ega', self.ega_client.docker, ega_path, ega_password, udt=ega_udt)
            if ega_transport_parallel != '1':
                self.logger.warning("Parallel streams on the EGA client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            self.ega_client.session = session
            uuids = self.get_uuids(file_data['ega'])
            return_code = self.ega_client.download(uuids, ega_username, ega_path, staging, ega_transport_parallel,
                                                   ega_udt, password=ega_password)
            session = self.cleanup('EGA', return_code, staging, output, self.ega_client)

        if 'collaboratory' in file_data and file_data['collaboratory']:
            check_access(self, icgc_token, 'icgc', self.icgc_client.docker, icgc_path)
            self.icgc_client.session = session
            uuids = self.get_uuids(file_data['collaboratory'])
            return_code = self.icgc_client.download(uuids, icgc_token, icgc_path, staging, icgc_transport_parallel,
                                                    file_from=icgc_transport_file_from, repo='collab')
            session = self.cleanup('ICGC', return_code, staging, output, self.icgc_client)

        if 'pdc' in file_data and file_data['pdc']:
            check_access(self, pdc_key, 'pdc', self.pdc_client.docker, pdc_path, secret_key=pdc_secret_key)
            urls = []
            for object_id in file_data['pdc']:
                urls.append(file_data['pdc'][object_id]['fileUrl'])
            self.pdc_client.session = session
            return_code = self.pdc_client.download(urls, pdc_key, pdc_path, staging, pdc_transport_parallel,
                                                   secret_key=pdc_secret_key)
            session = self.cleanup('PDC files', return_code, staging, output, self.pdc_client)

        if 'gdc' in file_data and file_data['gdc']:
            check_access(self, gdc_token, 'gdc', self.gdc_client.docker, gdc_path, udt=gdc_udt)
            uuids = self.get_uuids(file_data['gdc'])
            self.gdc_client.session = session
            return_code = self.gdc_client.download(uuids, gdc_token, gdc_path, staging, gdc_transport_parallel,
                                                   gdc_udt)
            self.check_code('Gdc', return_code)
        self.move_files(staging, output)

    def check_code(self, client, code):
        if code == 127:
            self.logger.error("Error connecting to the docker container.")
            raise click.ClickException("Please check the status of your docker client")
        elif code != 0:
            self.logger.error("%s client exited with a nonzero error code %s.", client, code)
            raise click.ClickException("Please check client output for error messages")

    def size_check(self, size, output):
        if output:
            free = psutil.disk_usage(output)[2]
            if free <= size:
                self.logger.error("Not enough space detected for download of %s. %s of space in %s",
                                  ''.join(convert_size(size)), ''.join(convert_size(free)), output)

    @staticmethod
    def get_uuids(file_data):
        uuids = []
        for object_id in file_data:
            uuids.append(file_data[object_id]['uuid'])
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
        for staged_file in os.listdir(staging):
            if staged_file != "state.json":
                try:
                    shutil.move(os.path.join(staging, staged_file), output)
                except shutil.Error:
                    self.logger.warning('File %s already present in download directory', staged_file)
                    os.remove(os.path.join(staging, staged_file))

    def cleanup(self, name, return_code, staging, output, client):
        self.check_code(name, return_code)
        self.move_files(staging, output)
        return client.session
