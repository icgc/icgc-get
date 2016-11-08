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

from icgcget.clients.ega.ega_client import EgaDownloadClient
from icgcget.clients.gdc.gdc_client import GdcDownloadClient
from icgcget.clients.gnos.gnos_client import GnosDownloadClient
from icgcget.clients.icgc.storage_client import StorageClient
from icgcget.clients.pdc.pdc_client import PdcDownloadClient
from icgcget.version import __version__


def versions_command(ctx, gnos_path, ega_path, gdc_path, icgc_path, pdc_path, container_version):
    """
    Function that controls the outputs of the versions command and creates download client objects.
    :param ctx:
    :param gnos_path:
    :param ega_path:
    :param gdc_path:
    :param icgc_path:
    :param pdc_path:
    :param container_version:
    :return:
    """
    docker = ctx.obj['docker']
    log_dir = ctx.obj['logdir']

    logger = logging.getLogger('__log__')
    logger.info('ICGC-Get Version: %s', __version__)
    logger.info('Clients:')
    json_path = log_dir + '/state.json'
    check_version_path(PdcDownloadClient(json_path, docker, container_version=container_version, log_dir=log_dir),
                       'PDC', pdc_path)
    check_version_path(EgaDownloadClient(json_path, docker, container_version=container_version, log_dir=log_dir),
                       'EGA', ega_path)
    check_version_path(GdcDownloadClient(json_path, docker, container_version=container_version, log_dir=log_dir),
                       'GDC', gdc_path)
    check_version_path(GnosDownloadClient(json_path, docker, container_version=container_version, log_dir=log_dir),
                       'GNOS', gnos_path)
    check_version_path(StorageClient(json_path, docker, container_version=container_version, log_dir=log_dir),
                       'ICGC', icgc_path)


def check_version_path(client, name, path):
    """
    Checks if path is valid then calls client's print_version command or throws error if path invalid.  Skips if no path
    provided for the client
    :param client:
    :param name:
    :param path:
    :return:
    """
    logger = logging.getLogger('__log__')
    if path:
        if os.path.isfile(path) or client.docker:
            client.print_version(path)
        else:
            logger.warning('Path "%s" to %s client could not be resolved.', path, name)
