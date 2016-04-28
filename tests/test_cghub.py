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

from click.testing import CliRunner
from conftest import file_test, get_info
from icgcget import cli


class TestCGHubMethods():
    def test_cghub(self, config, data_dir):
        runner = CliRunner()
        rc = runner.invoke(cli, [config, 'cghub', 'a337c425-4314-40c6-a40a-a444781bd1b7','--output', data_dir])
        file_info = get_info(data_dir, 'a337c425-4314-40c6-a40a-a444781bd1b7/G28034.MDA-MB-361.1.bam')
        assert file_test(file_info, 5159984257)

    def test_cghub_double(self, config, data_dir):
        runner = CliRunner()
        rc = runner.invoke(cli, [config, 'cghub', 'a452b625-74f6-40b5-90f8-7fe6f32b89bd',
                                 'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa', '--output', data_dir])
        file1_info = get_info(data_dir, 'a105a6ec-7cc3-4c3b-a99f-af29de8a7caa/C836.BICR_18.2.bam')
        file2_info = get_info(data_dir, 'a452b625-74f6-40b5-90f8-7fe6f32b89bd/C836.PEER.1.bam')
        assert (file_test(file1_info, 8163241177) and file_test(file2_info, 8145679575))

    def test_cghub_manifest(self, config, data_dir, manifest_dir):
        runner = CliRunner()
        rc = runner.invoke(cli, [config, 'cghub', manifest_dir + 'manifest.xml', '-m', '--output', data_dir])
        file1_info = get_info(data_dir, 'fcfc5e01-19a3-45de-ab4b-5440f49c6340/C836.MDA-MB-436.1.bam')
        file2_info = get_info(data_dir, 'f135768c-ffdf-4743-bb62-226131776b83/C836.NCC-StC-K140.1.bam')

        assert file_test(file1_info, 5191968) and file_test(file2_info, 7864608923)
