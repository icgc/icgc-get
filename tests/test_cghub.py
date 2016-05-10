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


def test_cghub(config, data_dir):
    download_test(['FI99990'], 'cghub', ['TCGA-DQ-5624-01A-01R-1872-13_mirna.bam'], [435700000], config, data_dir)


def test_cghub_double(config, data_dir):
    file_names = ['f3d43f0e-f734-47d5-954e-ed847b463c2c.sorted_genome_alignments.bam',
                  'TCGA-CV-6938-01A-11R-1914-13_mirna.bam']
    download_test(['FI99996', 'FI99994'], 'cghub', file_names, [3520000000, 97270000], config, data_dir)


def test_cghub_manifest(config, data_dir):
    file_names = ['TCGA-DQ-5624-01A-01R-1872-13_mirna.bam',
                  'f3d43f0e-f734-47d5-954e-ed847b463c2c.sorted_genome_alignments.bam',
                  'TCGA-CV-6938-01A-11R-1914-13_mirna.bam']
    download_manifest("950f60eb-1908-4b79-9b5a-060c5a29c3ae", file_names, [435700000, 3520000000, 97270000], config,
                      data_dir)
