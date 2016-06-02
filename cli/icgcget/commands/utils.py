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
import click

from cli.icgcget.clients import errors
from cli.icgcget.clients import portal_client


def filter_manifest_ids(self, manifest_json, repos):
    fi_ids = []  # Function to return a list of unique  file ids from a manifest.  Throws error if not unique
    for repo_info in manifest_json["entries"]:
        if repo_info["repo"] in repos:
            for file_info in repo_info["files"]:
                if file_info["id"] in fi_ids:
                    self.logger.error("Supplied manifest has repeated file identifiers.  Please specify a " +
                                      "list of repositories to prioritize")
                    raise click.Abort
                else:
                    fi_ids.append(file_info["id"])
    if not fi_ids:
        self.logger.warning("Files on manifest are not found on specified repositories")
        raise click.Abort
    return fi_ids


def get_manifest_json(self, file_ids, api_url, repos):
    if len(file_ids) > 1:
        self.logger.warning("For download from manifest files, multiple manifest id arguments is not supported")
        raise click.BadArgumentUsage("Multiple manifest files specified.")
    portal = portal_client.IcgcPortalClient()
    manifest_json = api_error_catch(self, portal.get_manifest_id, file_ids[0], api_url, repos)
    return manifest_json


def check_access(self, access, name, path="Default"):
    if access is None:
        self.logger.error("No credentials provided for the {} repository".format(name))
        raise click.BadParameter("Please provide credentials for {}".format(name))
    if path is None:
        self.logger.error("Path to {} download client not provided.".format(name))
        raise click.BadParameter("Please provide a path to the {} download client".format(name))


def api_error_catch(self, func, *args):
    try:
        return func(*args)
    except errors.ApiError as e:
        self.logger.error(e.message)
        raise click.Abort
