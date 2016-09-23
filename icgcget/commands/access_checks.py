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
import click
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.errors import SubprocessError
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.errors import ApiError
from icgcget.commands.utils import check_access


class AccessCheckDispatcher(object):
    """
    Dispatcher that controls verification of access commands
    """

    def __init__(self):
        self.logger = logging.getLogger('__log__')

    def access_checks(self, repo_list, file_data, gnos_key_icgc, gnos_key_tcga, gnos_key_barcelona, gnos_key_heidelberg,
                      gnos_key_london, gnos_key_cghub, gnos_key_seoul, gnos_key_tokyo, gnos_path, ega_username,
                      ega_password, gdc_token, icgc_token, pdc_key, pdc_secret_key, pdc_path, output, docker, api_url,
                      verify, container_version=''):
        """
        Dispatcher for access check functions of all repositories
        """
        gdc_client = GdcDownloadClient(verify=verify)
        ega_client = EgaDownloadClient(verify=verify)
        gt_client = GnosDownloadClient(docker=docker, container_version=container_version)
        icgc_client = StorageClient(verify=verify)
        pdc_client = PdcDownloadClient(docker=docker, container_version=container_version)

        if "collaboratory" in repo_list:
            self.access_check('collaboratory', icgc_token, icgc_client, api_url=api_url, code='collab')

        if "aws-virginia" in repo_list:
            self.access_check('aws-virginia', icgc_token, icgc_client, api_url=api_url, code='aws')

        if 'ega' in repo_list:
            self.access_check('ega', ega_username, ega_client, password=ega_password)

        if 'gdc' in repo_list:
            self.access_check_ids('gdc', file_data, gdc_token, gdc_client)

        if 'pcawg-chicago-icgc' in repo_list:
            self.access_check_ids('pcawg-chicago-icgc', file_data, gnos_key_icgc, gt_client, gnos_path, output)
        if 'pcawg-chicago-tcga' in repo_list:
            self.access_check_ids('pcawg-chicago-tcga', file_data, gnos_key_tcga, gt_client, gnos_path, output)
        if 'pcawg-barcelona' in repo_list:
            self.access_check_ids('pcawg-barcelona', file_data, gnos_key_barcelona, gt_client, gnos_path, output)
        if 'pcawg-heidelberg' in repo_list:
            self.access_check_ids('pcawg-heidelberg', file_data, gnos_key_heidelberg, gt_client, gnos_path, output)
        if 'pcawg-london' in repo_list:
            self.access_check_ids('pcawg-london', file_data, gnos_key_london, gt_client, gnos_path, output)
        if 'pcawg-cghub' in repo_list:
            self.access_check_ids('pcawg-cghub', file_data, gnos_key_cghub, gt_client, gnos_path, output)
        if 'pcawg-seoul' in repo_list:
            self.access_check_ids('pcawg-seoul', file_data, gnos_key_seoul, gt_client, gnos_path, output)
        if 'pcawg-tokyo' in repo_list:
            self.access_check_ids('pcawg-tokyo', file_data, gnos_key_tokyo, gt_client, gnos_path, output)

        if 'pdc' in repo_list:
            self.access_check_ids('pdc', file_data, pdc_key, pdc_client, pdc_path, output, pdc_secret_key)

    def access_response(self, result, repo):
        """
        Logs formatted output based on result of access check function
        :param result:
        :param repo:
        :return:
        """
        if result:
            self.logger.info('Valid access to the ' + repo)
        else:
            self.logger.info('Invalid access to the ' + repo)

    def access_check(self, repo, token, client, api_url=None, password=None, code=None):
        """
        Access check for clients that allow access checks for the entire repository isntead of single files.  Used by
        ega and icgc repositories
        :param repo:
        :param token:
        :param client:
        :param api_url:
        :param password:
        :param code:
        :return:
        """
        check_access(self, token, repo)
        try:
            self.access_response(client.access_check(token, repo=code, api_url=api_url, password=password),
                                 repo.upper())
        except ApiError:
            self.logger.error('Unable to connect to the %s API, cannot determine status of access credentials',
                              repo.upper())

    def access_check_ids(self, repo, file_data, key, client, path=None, output=None, secret_key="Default"):
        """
        Access check for clients that can only verify individual files.  uUed by pdc, gdc, and gnos
        :param repo:
        :param file_data:
        :param key:
        :param client:
        :param path:
        :param output:
        :param secret_key:
        :return:
        """
        if repo in file_data:
            if repo == 'pdc':
                uuids = [data['fileUrl'] for data in file_data[repo].values()]
            else:
                uuids = [data['uuid'] for data in file_data[repo].values()]
            if not uuids:
                self.logger.info('None of the specified ids will be downloaded from the %s repository:' +
                                 'unable to verify access credentials.', repo)
                return
            check_access(self, key, repo, path, secret_key=secret_key)
            try:
                self.access_response(client.access_check(key, uuids, path, output=output, repo=repo,
                                                         secret_key=secret_key),
                                     repo.upper() + ' files: {}'.format(', '.join(file_data[repo].keys())))
            except SubprocessError as ex:
                self.logger.error(ex.message)
                raise click.Abort
            except ApiError:
                raise click.Abort
