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
from collections import OrderedDict
from tabulate import tabulate
from icgcget.clients.utils import convert_size, donor_addition, increment_types, build_table, search_recursive


class StatusScreenDispatcher(object):
    def __init__(self):
        self.logger = logging.getLogger("__log__")

    def summary_table(self, file_data, output, table_format):
        repos = file_data.keys()

        type_counts = {"total": 0}
        download_count = {'total': 0}
        type_donors = {"total": []}
        type_sizes = OrderedDict({"total": 0})

        if output:
            headers = ["", "Size", "Unit", "File Count", "Donor Count", "Downloaded Files"]
        else:
            headers = ["", "Size", "Unit", "File Count", "Donor Count"]
        summary_table = []

        for repository in repos:
            repo_sizes = OrderedDict({"total": 0})
            repo_counts = {"total": 0}
            repo_donors = {"total": []}
            repo_download_count = {"total": 0}
            for file_id in file_data[repository].values():
                size = file_id["size"]

                data_type = file_id["dataType"]
                state = search_recursive(file_id["fileName"], output)
                type_sizes = increment_types(data_type, type_sizes, size)
                type_counts = increment_types(data_type, type_counts, 1)
                repo_sizes = increment_types(data_type, repo_sizes, size)
                repo_counts = increment_types(data_type, repo_counts, 1)
                if state:
                    download_count = increment_types(data_type, download_count, 1)
                    repo_download_count = increment_types(data_type, repo_download_count, 1)
                for donor in file_id['donors']:
                    repo_donors = donor_addition(repo_donors, donor, data_type)
                    type_donors = donor_addition(type_donors, donor, data_type)

            summary_table = build_table(summary_table, repository, repo_sizes, repo_counts, repo_donors,
                                        repo_download_count, output)
        summary_table = build_table(summary_table, 'Total', type_sizes, type_counts, type_donors, download_count,
                                    output)
        self.print_table(headers, summary_table, table_format)

    def file_table(self, file_data, output, table_format):
        repos = file_data.keys()
        headers = ["", "Size", "Unit", "File Format", "Data Type", "Repo", "Donor", "File Name", "Downloaded"]
        file_table = []
        for repository in repos:
            for file_id in file_data[repository]:
                data = file_data[repository][file_id]
                size = data["size"]
                if len(data['donors']) > 1:
                    donor = str(len(data['donors'])) + ' donors'
                else:
                    donor = data['donors'][0]['donorId']
                data_type = data["dataType"]
                if search_recursive(data["fileName"], output):
                    state = "Yes"
                else:
                    state = "No"
                file_size = convert_size(size)
                file_table.append([file_id, file_size[0], file_size[1], data["fileFormat"],
                                   data_type, repository, donor, data["fileName"], state])

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
