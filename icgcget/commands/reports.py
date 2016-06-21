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
from tabulate import tabulate
from icgcget.commands.utils import match_repositories, get_entities
from icgcget.clients.utils import convert_size, donor_addition, increment_types, build_table, search_recursive


class StatusScreenDispatcher(object):
    def __init__(self):
        self.logger = logging.getLogger("__log__")

    def summary_table(self, object_ids, output, api_url, table_format, verify):
        repos = object_ids.keys()
        repo_counts = {}
        repo_sizes = {}
        repo_donors = {}
        repo_download_count = {}

        type_counts = {"total": 0}
        download_count = {'total': 0}
        type_donors = {"total": []}
        type_sizes = OrderedDict({"total": 0})

        repo_list = []
        if output:
            headers = ["", "Size", "Unit", "File Count", "Donor Count", "Downloaded Files"]
        else:
            headers = ["", "Size", "Unit", "File Count", "Donor Count"]
        summary_table = []

        for repository in repos:
            repo_sizes[repository] = OrderedDict({"total": 0})
            repo_counts[repository] = {"total": 0}
            repo_donors[repository] = {"total": []}
            repo_download_count[repository] = {"total": 0}
        entities = get_entities(self, object_ids, api_url, verify)

        for entity in entities:
            state = False
            size = entity["fileCopies"][0]["fileSize"]
            repository, copy = match_repositories(self, repos, entity)
            data_type = entity["dataCategorization"]["dataType"]
            state = search_recursive(copy["fileName"], output)
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
                                        repo_download_count[repo], output)
            repo_list.append(repo)

        summary_table = build_table(summary_table, 'Total', type_sizes, type_counts, type_donors, download_count,
                                    output)
        self.print_table(headers, summary_table, table_format)

    def file_table(self, object_ids, output, api_url, table_format, verify):
        repos = object_ids.keys()
        headers = ["", "Size", "Unit", "File Format", "Data Type", "Repo", "Donor", "File Name", "Downloaded"]
        file_table = []
        entities = get_entities(self, object_ids, api_url, verify)
        for entity in entities:
            size = entity["fileCopies"][0]["fileSize"]
            repository, copy = match_repositories(self, repos, entity)
            data_type = entity["dataCategorization"]["dataType"]
            if search_recursive(copy["fileName"], output):
                state = "Yes"
            else:
                state = "No"
            file_size = convert_size(size)
            file_table.append([entity["id"], file_size[0], file_size[1], copy["fileFormat"],
                               data_type, repository, entity["donors"][0]['donorId'], copy["fileName"], state])

        self.print_table(headers, file_table, table_format)

    def print_table(self, headers, file_table, table_format):
        if table_format == 'tsv':
            for line in file_table:
                line = [str(item) for item in line]
                self.logger.info('  '.join(line))
        elif table_format == 'pretty':
            file_table = [headers] + file_table
            self.logger.info(tabulate(file_table, headers="firstrow", tablefmt="fancy_grid", numalign="right"))
        elif table_format == 'json':
            json_dict = {}
            for line in file_table:
                line_dict = {}
                for i in range(1, len(headers)):
                    line_dict[headers[i]] = line[i]
                json_dict[line[0]] = line_dict
            print json_dict
