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
import click
import os
from collections import OrderedDict
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.errors import SubprocessError
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.utils import convert_size, donor_addition, increment_types, build_table

from tabulate import tabulate

from utils import check_access, api_error_catch,  get_entities


class StatusScreenDispatcher:
    def __init__(self):
        self.logger = logging.getLogger("__log__")

    def summary_table(self, repos, file_ids, manifest, api_url, output, tsv):
        repo_counts = {}
        repo_sizes = {}
        repo_donors = {}
        repo_download_count = {}

        type_counts = {"total": 0}
        download_count = {'total': 0}
        type_donors = {"total": []}
        type_sizes = OrderedDict({"total": 0})

        repo_list = []
        summary_table = [["", "Size", "Unit", "File Count", "Donor Count", "Downloaded Files"]]
        for repository in repos:
            repo_sizes[repository] = OrderedDict({"total": 0})
            repo_counts[repository] = {"total": 0}
            repo_donors[repository] = {"total": []}
            repo_download_count[repository] = {"total": 0}

        entities = get_entities(self, manifest, file_ids, api_url, repos)
        for entity in entities:
            size = entity["fileCopies"][0]["fileSize"]
            repository, copy = self.match_repositories(repos, entity)
            data_type = entity["dataCategorization"]["dataType"]
            state = copy["fileName"] in os.listdir(output)
            type_sizes = increment_types(data_type, type_sizes, size)
            type_counts = increment_types(data_type, type_counts, 1)
            repo_sizes[repository] = increment_types(data_type, repo_sizes[repository], size)
            repo_counts[repository] = increment_types(data_type, repo_counts[repository], 1)

            if state:
                download_count = increment_types(data_type, download_count, 1)
                repo_download_count[repository] = increment_types(data_type, repo_download_count[repository], 1)
            for donor_info in entity['donors']:
                repo_donors[repository] = donor_addition(repo_donors[repository], donor_info, data_type)
                type_donors = donor_addition(type_donors, donor_info, data_type)

        for repo in repo_sizes:
            summary_table = build_table(summary_table, repo, repo_sizes[repo], repo_counts[repo], repo_donors[repo],
                                        repo_download_count[repo])
            repo_list.append(repo)
        summary_table = build_table(summary_table, 'Total', type_sizes, type_counts, type_donors, download_count)
        if tsv:
            for line in summary_table:
                line = map(str, line)
                self.logger.info('  '.join(line))
        else:
            self.logger.info(tabulate(summary_table, headers="firstrow", numalign="right"))

    def file_table(self, repos, file_ids, manifest, api_url, output, tsv):
        file_table = [["", "Size", "Unit", "File Format", "Data Type", "Repo", "File Name", "Downloaded"]]
        entities = get_entities(self, manifest, file_ids, api_url, repos)

        for entity in entities:
            size = entity["fileCopies"][0]["fileSize"]
            repository, copy = self.match_repositories(repos, entity)
            data_type = entity["dataCategorization"]["dataType"]
            if copy["fileName"] in os.listdir(output):
                state = "Yes"
            else:
                state = "No"
            file_size = convert_size(size)
            file_table.append([entity["id"], file_size[0], file_size[1], copy["fileFormat"],
                               data_type, repository, copy["fileName"], state])
        if tsv:
            for line in file_table:
                line = map(str, line)
                self.logger.info('  '.join(line))
        else:
            self.logger.info(tabulate(file_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))

    def access_checks(self, repo_list, file_ids, manifest, cghub_access, cghub_path, ega_access, gdc_access,
                      icgc_access, pdc_access, pdc_path, pdc_region, output, api_url):
        cghub_ids = []
        gdc_ids = []
        pdc_urls = []

        gdc_client = GdcDownloadClient()
        ega_client = EgaDownloadClient()
        gt_client = GnosDownloadClient()
        icgc_client = StorageClient()
        pdc_client = PdcDownloadClient()

        entities = get_entities(self, manifest, file_ids, api_url, repo_list)
        for entity in entities:
            repository, copy = self.match_repositories(repo_list, entity)
            if repository == "gdc":
                gdc_ids.append(entity["dataBundle"]["dataBundleId"])
            if repository == "cghub":
                cghub_ids.append(entity["dataBundle"]["dataBundleId"])
            if repository == "pdc":
                pdc_urls.append('s3' + copy['repoBaseUrl'][5:] + copy["repoDataPath"])

        if "collaboratory" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(icgc_client.access_check(icgc_access, repo="collab", api_url=api_url),
                                 "Collaboratory.")
        if "aws-virginia" in repo_list:
            check_access(self, icgc_access, "icgc")
            self.access_response(icgc_client.access_check(icgc_access, repo="aws", api_url=api_url),
                                 "Amazon Web Server.")
        if 'ega' in repo_list:
            check_access(self, ega_access, 'ega')
            self.access_response(ega_client.access_check(ega_access), "EGA.")

        if 'gdc' in repo_list and gdc_ids:
            check_access(self, gdc_access, 'gdc')
            gdc_result = api_error_catch(self, gdc_client.access_check, gdc_access, gdc_ids)
            self.access_response(gdc_result, "GDC files specified.")

        if 'cghub' in repo_list and cghub_ids:  # as before, can't check cghub permissions without files
            check_access(self, cghub_access, 'cghub', cghub_path)

            try:
                self.access_response(gt_client.access_check(cghub_access, cghub_ids, cghub_path, output=output),
                                     "CGHub files.")
            except SubprocessError as e:
                self.logger.error(e.message)
                raise click.Abort

        if 'pdc' in repo_list and pdc_urls:
            check_access(self, pdc_access, 'pdc', pdc_path)
            try:
                self.access_response(pdc_client.access_check(pdc_access, pdc_urls, pdc_path, output=output,
                                                             region=pdc_region), "PDC files.")
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
