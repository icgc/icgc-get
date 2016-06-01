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
from collections import OrderedDict
import click
from icgcget.clients import portal_client
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.errors import SubprocessError
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.utils import convert_size, donor_addition, increment_types, build_table
from tabulate import tabulate

from utils import check_access, api_error_catch, filter_manifest_ids, get_manifest_json


class StatusScreenDispatcher:
    def __init__(self):
        self.logger = logging.getLogger("__log__")
        self.gdc_client = GdcDownloadClient()
        self.ega_client = EgaDownloadClient()
        self.gt_client = GnosDownloadClient()
        self.icgc_client = StorageClient()
        self.pdc_client = PdcDownloadClient()

        self.cghub_ids = []
        self.gdc_ids = []
        self.pdc_urls = []

    def status_tables(self, repos, file_ids, manifest, api_url, no_files):
        repo_counts = {}
        repo_sizes = {}
        repo_donors = {}

        type_counts = {"total": 0}
        type_donors = {"total": []}
        type_sizes = OrderedDict({"total": 0})

        repo_list = []

        file_table = [["", "Size", "Unit", "File Format", "Data Type", "Repo"]]
        summary_table = [["", "Size", "Unit", "File Count", "Donor Count"]]
        if manifest:
            manifest_json = get_manifest_json(self, file_ids, api_url, repos)
            file_ids = filter_manifest_ids(self, manifest_json, repos)

        for repository in repos:
            repo_sizes[repository] = OrderedDict({"total": 0})
            repo_counts[repository] = {"total": 0}
            repo_donors[repository] = {"total": []}

        portal = portal_client.IcgcPortalClient()
        entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)

        for entity in entities:
            size = entity["fileCopies"][0]["fileSize"]
            repository, copy = self.match_repositories(repos, entity)
            data_type = entity["dataCategorization"]["dataType"]

            if not no_files:
                file_size = convert_size(size)
                file_table.append([entity["id"], file_size[0], file_size[1], copy["fileFormat"],
                                   data_type, repository])

            type_sizes = increment_types(data_type, type_sizes, size)
            type_counts = increment_types(data_type, type_counts, 1)
            repo_sizes[repository] = increment_types(data_type, repo_sizes[repository], size)
            repo_counts[repository] = increment_types(data_type, repo_counts[repository], 1)

            for donor_info in entity['donors']:
                repo_donors[repository] = donor_addition(repo_donors[repository], donor_info, data_type)
                type_donors = donor_addition(type_donors, donor_info, data_type)

            if repository == "gdc":
                self.gdc_ids.append(entity["dataBundle"]["dataBundleId"])
            if repository == "cghub":
                self.cghub_ids.append(entity["dataBundle"]["dataBundleId"])
            if repository == "pdc":
                self.pdc_urls.append('s3' + copy['repoBaseUrl'][5:] + copy["repoDataPath"])

        for repo in repo_sizes:
            summary_table = build_table(summary_table, repo, repo_sizes[repo], repo_counts[repo], repo_donors[repo])
            repo_list.append(repo)
        summary_table = build_table(summary_table, 'Total', type_sizes, type_counts, type_donors)

        if not no_files:
            self.logger.info(tabulate(file_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
        self.logger.info(tabulate(summary_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))

        return repo_list

    def access_checks(self, repo_list, cghub_access, cghub_path, ega_access, gdc_access, icgc_access, pdc_access,
                      pdc_path, pdc_region, output, api_url):
        if "collaboratory" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="collab", api_url=api_url),
                                 "Collaboratory.")
        if "aws-virginia" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(self.icgc_client.access_check(icgc_access, repo="aws", api_url=api_url),
                                 "Amazon Web server.")
        if 'ega' in repo_list:
            check_access(self, ega_access, 'ega')
            self.access_response(self.ega_client.access_check(ega_access), "ega.")

        if 'gdc' in repo_list and self.gdc_ids:
            check_access(self, gdc_access, 'gdc')
            gdc_result = api_error_catch(self, self.gdc_client.access_check, gdc_access, self.gdc_ids)
            self.access_response(gdc_result, "gdc files specified.")

        if 'cghub' in repo_list and self.cghub_ids:  # as before, can't check cghub permissions without files
            check_access(self, cghub_access, 'cghub', cghub_path)
            try:
                self.access_response(self.gt_client.access_check(cghub_access, self.cghub_ids, cghub_path,
                                                                 output=output), "cghub files.")
            except SubprocessError as e:
                self.logger.error(e.message)
                raise click.Abort

        if 'pdc' in repo_list and self.pdc_urls:
            check_access(self, pdc_access, 'pdc', pdc_path)
            try:
                self.access_response(self.pdc_client.access_check(pdc_access, self.pdc_urls, pdc_path, output=output,
                                                                  region=pdc_region), "pdc files.")
            except SubprocessError as e:
                self.logger.error(e.message)
                raise click.Abort

    def match_repositories(self, repos, copies):
        for repository in repos:
            for copy in copies["fileCopies"]:
                if repository == copy["repoCode"]:
                    return repository, copy
        self.logger.error("File {} not found on repositories {}".format(copies["id"], repos))
        raise click.Abort

    def access_response(self, result, repo):
        if result:
            self.logger.info("Valid access to the " + repo)
        else:
            self.logger.info("Invalid access to the " + repo)
