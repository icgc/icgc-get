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

    def access_checks(self, ctx, file_data, docker, api_url, container_version=''):
        """
        Dispatcher for access check functions of all repositories
        """
        params = ctx.params
        verify = params['no_ssl_verify']
        repos = params['repos']
        output = params['output']
        gnos_path = params['gnos_path']

        gdc_client = GdcDownloadClient(verify=verify)
        ega_client = EgaDownloadClient(verify=verify)
        gt_client = GnosDownloadClient(docker=docker, container_version=container_version)
        icgc_client = StorageClient(verify=verify)
        pdc_client = PdcDownloadClient(docker=docker, container_version=container_version)


        if 'collaboratory' in repos:
            self.access_check('collaboratory', params['icgc_token'], icgc_client, api_url=api_url, code='collab')

        if 'aws-virginia' in repos:
            self.access_check('aws-virginia', params['icgc_token'], icgc_client, api_url=api_url, code='aws')

        if 'ega' in repos:
            self.access_check('ega', params['ega_username'], ega_client, password=params['ega_password'])

        if 'gdc' in repos:
            self.access_check_ids('gdc', file_data, params['gdc_token'], gdc_client)

        if 'pcawg-chicago-icgc' in repos:
            self.access_check_ids('pcawg-chicago-icgc', file_data, params['gnos_key_icgc'],
                                  gt_client, gnos_path, output)
        if 'pcawg-chicago-tcga' in repos:
            self.access_check_ids('pcawg-chicago-tcga', file_data, params['gnos_key_tcga'],
                                  gt_client, gnos_path, output)
        if 'pcawg-barcelona' in repos:
            self.access_check_ids('pcawg-barcelona', file_data, params['gnos_key_barcelona'],
                                  gt_client, gnos_path, output)
        if 'pcawg-heidelberg' in repos:
            self.access_check_ids('pcawg-heidelberg', file_data, params['gnos_key_heidelberg'],
                                  gt_client, gnos_path, output)
        if 'pcawg-london' in repos:
            self.access_check_ids('pcawg-london', file_data, params['gnos_key_london'], gt_client, gnos_path, output)
        if 'pcawg-cghub' in repos:
            self.access_check_ids('pcawg-cghub', file_data, params['gnos_key_cghub'], gt_client, gnos_path, output)
        if 'pcawg-seoul' in repos:
            self.access_check_ids('pcawg-seoul', file_data, params['gnos_key_seoul'], gt_client, gnos_path, output)
        if 'pcawg-tokyo' in repos:
            self.access_check_ids('pcawg-tokyo', file_data, params['gnos_key_tokyo'], gt_client, gnos_path, output)

        if 'pdc' in repos:
            self.access_check_ids('pdc', file_data, params['pdc_key'], pdc_client, params['pdc_path'], output,
                                  params['pdc_secret'])

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
        Access check for clients that allow access checks for the entire repository instead of single files.  Used by
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
            except ApiError as api_error:
                self.logger.error(api_error.message)
                raise click.Abort
