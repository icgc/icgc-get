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
from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.errors import SubprocessError
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.portal_client import IcgcPortalClient
from icgcget.commands.utils import check_access, api_error_catch, get_manifest_json, filter_manifest_ids, \
    match_repositories


class AccessCheckDispatcher(object):
    def __init__(self):
        self.logger = logging.getLogger("__log__")
        self.cghub_ids = []
        self.gdc_ids = []
        self.pdc_urls = []

    def access_checks(self, repo_list, file_ids, manifest, cghub_key, cghub_path, ega_username, ega_password,
                      gdc_token, icgc_token, pdc_key, pdc_secret_key, pdc_path, output, api_url, verify):

        gdc_client = GdcDownloadClient(verify=verify)
        ega_client = EgaDownloadClient(verify=verify)
        gt_client = GnosDownloadClient()
        icgc_client = StorageClient(verify=verify)
        pdc_client = PdcDownloadClient()

        if 'gdc' in repo_list or 'cghub' in repo_list or 'pdc' in repo_list:
            self.entity_search(manifest, file_ids, api_url, repo_list, verify)

        if "collaboratory" in repo_list:
            check_access(self, icgc_token, "icgc")
            self.access_response(icgc_client.access_check(icgc_token, repo="collab", api_url=api_url),
                                 "Collaboratory.")
        if "aws-virginia" in repo_list:
            check_access(self, icgc_token, "icgc")
            self.access_response(icgc_client.access_check(icgc_token, repo="aws", api_url=api_url),
                                 "Amazon Web Server.")
        if 'ega' in repo_list:
            check_access(self, ega_username, 'ega', password=ega_password)
            self.access_response(ega_client.access_check(ega_username, password=ega_password), "EGA.")

        if 'gdc' in repo_list:
            if self.id_check('gdc', self.gdc_ids):
                check_access(self, gdc_token, 'gdc')
                gdc_result = api_error_catch(self, gdc_client.access_check, gdc_token, self.gdc_ids)
                self.access_response(gdc_result, "GDC files specified.")

        if 'cghub' in repo_list:
            if self.id_check('cghub', self.cghub_ids):
                check_access(self, cghub_key, 'cghub', cghub_path)
                try:
                    self.access_response(gt_client.access_check(cghub_key, self.cghub_ids, cghub_path,
                                                                output=output), "CGHub files.")
                except SubprocessError as ex:
                    self.logger.error(ex.message)
                    raise click.Abort

        if 'pdc' in repo_list:
            if self.id_check('pdc', self.pdc_urls):
                check_access(self, pdc_key, 'pdc', pdc_path, secret_key=pdc_secret_key)
                try:
                    self.access_response(pdc_client.access_check(pdc_key, self.pdc_urls, pdc_path, output=output,
                                                                 secret_key=pdc_secret_key), "PDC files.")
                except SubprocessError as ex:
                    self.logger.error(ex.message)
                    raise click.Abort

    def access_response(self, result, repo):
        if result:
            self.logger.info("Valid access to the " + repo)
        else:
            self.logger.info("Invalid access to the " + repo)

    def id_check(self, repo, ids):
        if not ids:
            self.logger.info("None of the specified ids will be downloaded from the %s repository, " +
                             "unable to verify access credentials.", repo)
            return False
        else:
            return True

    def entity_search(self, manifest, file_ids, api_url, repo_list, verify):
        if file_ids:
            portal = IcgcPortalClient(verify)
            if manifest:
                manifest_json = get_manifest_json(self, file_ids, api_url, repo_list, portal)
                file_ids = filter_manifest_ids(self, manifest_json, repo_list)
            entities = api_error_catch(self, portal.get_metadata_bulk, file_ids, api_url)
            for entity in entities:
                repository, copy = match_repositories(self, repo_list, entity)
                if repository == "gdc":
                    self.gdc_ids.append(entity["dataBundle"]["dataBundleId"])
                if repository == "cghub":
                    self.cghub_ids.append(entity["dataBundle"]["dataBundleId"])
                if repository == "pdc":
                    self.pdc_urls.append('s3://' + copy["repoDataPath"])
