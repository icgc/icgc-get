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

import os
import tempfile
import threading

import pytest
from click.testing import CliRunner

from icgcget import cli
from tests.fixtures import stub_thread


@pytest.fixture(scope="session")
def config():
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    conf = path + "/config_dev.yaml"
    return conf


@pytest.fixture(scope="session")
def data_dir():
    return tempfile.gettempdir()


@pytest.fixture(scope="session")
def manifest_dir():
    manifest_directory = os.path.abspath(os.path.dirname(__file__)) + '/data/'
    return manifest_directory


def file_test(file_info, size):
    return file_info.st_size == size and oct(file_info.st_mode & 755)


def get_info(data, filename):
    if os.path.isfile(data + '/' + filename):
        file_info = os.stat(data + '/' + filename)
        return file_info
    else:
        assert filename is None  # Unable to download file as expected


def start_server():
    thread = stub_thread.stubThread(1, "TestThread")
    thread.start()


def stop_server():
    for thread in threading.enumerate():
        thread.join()


def download_test(file_id, repo, file_names, sizes, conf, data):
    runner = CliRunner()
    try:
        start_server()
    except Exception as e:
        assert e
    args = ['--config', conf, 'download']
    args.extend(file_id)
    args.extend(['-r', repo, '--output', data, '-y'])
    runner.env = dict(os.environ, ICGCGET_API_URL="http://127.0.0.1:8000/")
    rc = runner.invoke(cli.cli, args)
    if rc.exit_code != 0:
        assert rc.output == 0  # An error occurred during the download attempt
    for i in range(len(file_names)):
        file_info = get_info(data, file_names[i])
        result = file_test(file_info, sizes[i])
        if not result:
            assert file_test(file_info, sizes[i])  # File was not of the expected file size


def download_manifest(manifest_id, file_names, sizes, conf, data):
    runner = CliRunner()
    start_server()
    args = ['--config', conf, 'download', manifest_id, '-m', '--output', data, '-y']
    runner.env = dict(os.environ, ICGCGET_API_URL="http://127.0.0.1:8000/")
    rc = runner.invoke(cli.cli, args)
    if rc.exit_code != 0:
        assert rc.output == 0  # An error occurred during the download attempt
    for i in range(len(file_names)):
        file_info = get_info(data, file_names[i])
        result = file_test(file_info, sizes[i])
        if not result:
            assert file_test(file_info, sizes[i])  # File was not of the expected file size
