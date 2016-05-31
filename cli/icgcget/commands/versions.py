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

import icgcget.clients.ega.ega_client as ega_client
import icgcget.clients.gdc.gdc_client as gdc_client
import icgcget.clients.icgc.storage_client as storage_client
import icgcget.clients.pdc.pdc_client as pdc_client
import icgcget.clients.gnos.gnos_client as gnos_client


def versions_command(cghub_path, ega_access, ega_path, gdc_path, icgc_path, pdc_path, version_num):
    logger = logging.getLogger("__log__")
    pdc_client.PdcDownloadClient().print_version(pdc_path)
    gdc_client.GdcDownloadClient().print_version(gdc_path)
    ega_client.EgaDownloadClient().print_version(ega_path, ega_access)
    gnos_client.GnosDownloadClient().print_version(cghub_path)
    storage_client.StorageClient().print_version(icgc_path)
    logger.warning("ICGC-Get Version: {}".format(version_num))
