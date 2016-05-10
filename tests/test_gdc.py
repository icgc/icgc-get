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


from conftest import download_test, download_manifest


def test_gdc(config, data_dir):
    file_name = ['f483ad78-b092-4d10-9afb-eccacec9d9dc/TCGA-CH-5763-01A-11D-1572-02_AC1JWAACXX' +
                 '---TCGA-CH-5763-11A-01D-1572-02_AC1JWAACXX---Segment.tsv']
    download_test(['FIGDCID'], 'gdc', file_name, [1483], config, data_dir)


def test_gdc_double(config, data_dir):
    file_names = ['2c759eb8-7ee0-43f5-a008-de4317ab8c70/14-3-3_beta-R-V_GBL11066140.tif',
                  'a6b2f1ff-5c71-493c-b65d-e344ed29b7bb/14-3-3_beta-R-V_GBL11066140.txt']
    download_test(['FIGDCID2', 'FIGDCID2'], 'gdc', file_names, [6261580, 1399430], config, data_dir)


def test_gdc_manifest(config, data_dir):
    file_names = ['f483ad78-b092-4d10-9afb-eccacec9d9dc/TCGA-CH-5763-01A-11D-1572-02_AC1JWAACXX' +
                 '---TCGA-CH-5763-11A-01D-1572-02_AC1JWAACXX---Segment.tsv'
                 '2c759eb8-7ee0-43f5-a008-de4317ab8c70/14-3-3_beta-R-V_GBL11066140.tif',
                 'a6b2f1ff-5c71-493c-b65d-e344ed29b7bb/14-3-3_beta-R-V_GBL11066140.txt']
    download_manifest("ed78541a-0e3a-4d89-b348-f42886442aeb", file_names, [1483, 6261580, 1399430], config, data_dir)
