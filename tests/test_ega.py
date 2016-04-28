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


class TestEGAMethods():
    def test_ega(self, config, data_dir):
        runner = CliRunner()
        rc = runner.invoke(cli, [config, 'ega', 'EGAD00001001847', '--output', data_dir])
        file1_info = get_info(data_dir, '_EGAR00001385154_4Cseq_single-end_HD-MB03_TGFBR1_sequence.fastq.gz')
        file2_info = get_info(data_dir, '_EGAR00001385153_4Cseq_single-end_HD-MB03_SMAD9_sequence.fastq.gz')
        assert (file_test(file1_info, 323699429), file_test(file2_info, 447127561))

    def test_ega_file(self, config, data_dir):
        runner = CliRunner()
        rc = runner.invoke(cli, [config, 'ega', 'EGAF00000112559', '--output', data_dir])
        file_info = get_info(data_dir, '_methylationCEL_CLL-174.CEL')
        assert (file_test(file_info, 5556766))
