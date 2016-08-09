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
    def __init__(self, json_path=None, docker=False, log_dir=None, container_version=''):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient(json_path, docker, log_dir=log_dir, container_version=container_version)
        self.ega_client = EgaDownloadClient(json_path, docker, log_dir=log_dir, container_version=container_version)
        self.gt_client = GnosDownloadClient(json_path, docker, log_dir, container_version=container_version)
        self.pdc_client = PdcDownloadClient(json_path, docker, log_dir, container_version=container_version)
        self.icgc_client = StorageClient(json_path, docker, log_dir=log_dir, container_version=container_version)

    def download_manifest(self, repos, file_ids, manifest, output, api_url, verify, unique=False):
        """
        Function responsible for retrieving manifests and metadata from the icgc api and formatting that data into
        a download session object.  All queries to the portal go through this function.
        :param repos:
        :param file_ids:
        :param manifest:
        :param output:
        :param api_url: icgc-api url
        :param verify: toggles ssl verification
        :param unique: controls if all files on output manifest must be unique
        :return: download session
        """
        portal = portal_client.IcgcPortalClient(verify)
        manifest_json = self.get_manifest(manifest, file_ids, api_url, repos, portal)
        download_session = {'pid': os.getpid(), 'start_time': datetime.datetime.utcnow().isoformat(),
                            'subprocess': [], 'command': file_ids, 'container': 0}
        size, download_session = calculate_size(manifest_json, download_session)
        file_data = download_session['file_data']
        if manifest:
            file_ids = []
            for repo in file_data:
                file_ids.extend(file_data[repo].keys())
                self.logger.debug(' '.join(file_data[repo].keys()) + ' found on manifest')
        entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
        for entity in entities:
            repo, copy = match_repositories(self, repos, entity)
            if not repo:
                raise click.Abort()

            if copy['repoCode'] == repo:
                if unique and search_recursive(copy["fileName"], output):
                    file_data[repo].pop(entity['id'])
                    self.logger.info("File %s found in download directory, skipping", entity['id'])
                    continue
                temp_file = {'fileName': copy["fileName"], 'dataType': entity["dataCategorization"]["dataType"],
                             'donors': entity["donors"], 'fileFormat': copy['fileFormat']}

                if "fileName" in copy["indexFile"]:
                    temp_file['index_filename'] = copy["indexFile"]["fileName"]
                if repo == 'pdc':
                    file_data[repo][entity['id']]['fileUrl'] = 's3://' + copy['repoDataPath']
                    if unique and search_recursive(copy['repoDataPath'].split('/')[1], output):
                        file_data[repo].pop(entity['id'])
                        self.logger.info("File %s found in download directory, skipping", entity['id'])
                        continue
                file_data[repo][entity["id"]].update(temp_file)
                self.logger.debug('File %s added to file data under repo %s', entity['id'], repo)

        self.size_check(size, output)
        if not flatten_file_data(file_data):
            self.logger.error("All files were found in download directory, aborting")
            raise click.Abort
        return download_session

    def download(self, session, staging, output,
                 gnos_key_icgc, gnos_key_tcga, gnos_key_barcelona, gnos_key_heidelberg,
                 gnos_key_london, gnos_key_cghub, gnos_key_seoul, gnos_key_tokyo, gnos_path, gnos_transport_parallel,
                 ega_username, ega_password, ega_path, ega_transport_parallel, ega_udt,
                 gdc_token, gdc_path, gdc_transport_parallel, gdc_udt,
                 icgc_token, icgc_path, icgc_transport_file_from, icgc_transport_parallel,
                 pdc_key, pdc_secret_key, pdc_path, pdc_transport_parallel):
        """
        Function that manages client download calls, cleans up downloaded files, and passes updated session info
        between each process.
        """
        self.client_download('aws-virginia', icgc_token, icgc_path, self.icgc_client, session, staging, output,
                             icgc_transport_parallel, code='aws', transport_file_from=icgc_transport_file_from)

        self.client_download('collaboratory', icgc_token, icgc_path, self.icgc_client, session, staging, output,
                             icgc_transport_parallel, code='collab', transport_file_from=icgc_transport_file_from)

        self.client_download('gdc', gdc_token, gdc_path, self.gdc_client, session, staging, output,
                             gdc_transport_parallel, udt=gdc_udt)

        self.client_download('ega', ega_username, ega_path, self.ega_client, session, staging, output,
                             ega_transport_parallel, udt=ega_udt, password=ega_password)

        self.client_download('pcawg-barcelona', gnos_key_barcelona, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-barcelona')

        self.client_download('pcawg-cghub', gnos_key_cghub, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-cghub')

        self.client_download('pcawg-chicago-icgc', gnos_key_icgc, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-chicago-icgc')

        self.client_download('pcawg-chicago-tcga', gnos_key_tcga, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-chicago-tcga')

        self.client_download('pcawg-heidelberg', gnos_key_heidelberg, gnos_path, self.gt_client, session, staging,
                             output, gnos_transport_parallel, code='pcawg-heidelberg')

        self.client_download('pcawg-london', gnos_key_london, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-london')

        self.client_download('pcawg-seoul', gnos_key_seoul, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-seoul')

        self.client_download('pcawg-tokyo', gnos_key_tokyo, gnos_path, self.gt_client, session, staging, output,
                             gnos_transport_parallel, code='pcawg-tokyo')

        self.client_download('pdc', pdc_key, pdc_path, self.pdc_client, session, staging, output,
                             pdc_transport_parallel, secret_key=pdc_secret_key)

        return session

    def check_code(self, client, code):
        """
        Function used to parse error codes returned by docker containers and clients
        :param client:
        :param code:
        :return:
        """
        if code == 127:
            self.logger.error("Error connecting to the docker container.")
            raise click.ClickException("Please check the status of your docker client")
        elif code != 0:
            self.logger.error("%s client exited with a nonzero error code %s.", client, code)
            raise click.ClickException("Please check client output for error messages")

    def cleanup(self, name, return_code, staging, output):
        """
        Wrapper around download.move_files and download.check_code
        :param name:
        :param return_code:
        :param staging:
        :param output:
        :return:
        """
        self.check_code(name, return_code)
        self.move_files(staging, output)

    def client_download(self, repo, token, path, client, session, staging, output, transport_parallel,
                        transport_file_from=None, code=None, udt=True, password="Default", secret_key="Default"):
        """
        Generalized function handling argument verification, parsing, and cleanup for download from client
        :param repo:
        :param token:
        :param path:
        :param client:
        :param session:
        :param staging:
        :param output:
        :param transport_parallel:
        :param transport_file_from:
        :param code:
        :param udt:
        :param password:
        :param secret_key:
        :return:
        """
        file_data = session['file_data']
        if repo in file_data and file_data[repo]:
            check_access(self, token, repo, client.docker, path, udt, secret_key)
            self.icgc_client.session = session
            if repo == 'ega' and transport_parallel != '1':
                self.logger.warning("Parallel streams on the EGA client may cause reliability issues and failed " +
                                    "downloads.  This option is not recommended.")
            if repo == 'pdc':
                uuids = []
                for object_id in file_data[repo]:
                    uuids.append(file_data[repo][object_id]['fileUrl'])
            else:
                uuids = self.get_uuids(file_data[repo])
            return_code = client.download(uuids, token, path, staging, transport_parallel, repo=code, udt=udt,
                                          file_from=transport_file_from, password=password, secret_key=secret_key)
            self.cleanup(repo, return_code, staging, output)

    def size_check(self, size, output):
        """
        Function to check if projected download size is small enough for available disk space.
        :param size:
        :param output:
        :return:
        """
        if output:
            free = psutil.disk_usage(output)[2]
            if free <= size:
                self.logger.error("Not enough space detected for download of %s. %s of space in %s",
                                  ''.join(convert_size(size)), ''.join(convert_size(free)), output)
                click.Abort()

    @staticmethod
    def get_uuids(file_data):
        """
        Function used to extract all uuids from a file_data object
        :param file_data:
        :return:
        """
        uuids = []
        for object_id in file_data:
            uuids.append(file_data[object_id]['uuid'])
        return uuids

    def get_manifest(self, manifest, file_ids, api_url, repos, portal):
        """
        Function that calls the api for a manifest.json files and filters it for duplicates if necessary.
        :param manifest:
        :param file_ids:
        :param api_url:
        :param repos:
        :param portal:
        :return:
        """
        if manifest:
            manifest_json = get_manifest_json(self, file_ids, api_url, repos, portal)
        else:
            manifest_json = api_error_catch(self, portal.get_manifest, file_ids, api_url, repos)

        if not manifest_json["unique"] or len(manifest_json["entries"]) != 1:
            filter_manifest_ids(self, manifest_json, repos)
        return manifest_json

    def move_files(self, staging, output):
        """
        Function that moves files from staging to output and handles errors
        :param staging:
        :param output:
        :return:
        """
        for staged_file in os.listdir(staging):

            try:
                shutil.move(os.path.join(staging, staged_file), output)
            except shutil.Error:
                try:
                    self.logger.info('File %s already present in download directory', staged_file)
                    os.remove(os.path.join(staging, staged_file))
                except OSError:
                    self.logger.error('Insufficient permissions to move files. ' +
                                      'Please remove .staging from your download directory manually.')
