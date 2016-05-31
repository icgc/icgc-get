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


from conftest import download_test


def test_icgc(data_dir):
    file_name = ['fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618' +
                 '.germline.sv.vcf.gz/a5a6d87b-e599-528b-aea0-73f5084205d5',
                 'fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618.' +
                 'germline.sv.vcf.gz.tbi/efcb7a5c-ff36-5557-84a3-7d4aa0e416b8']
    download_test(['FI250134'], 'status', 'collaboratory', file_name, [202180, 21701],  data_dir)


def test_icgc_manifest(data_dir):
    file_name = ['fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618' +
                 '.germline.sv.vcf.gz/a5a6d87b-e599-528b-aea0-73f5084205d5',
                 'fc447d55-95d8-0b34-e040-11ac0d483afa.embl-delly_1-0-0-preFilter.20150618.' +
                 'germline.sv.vcf.gz.tbi/efcb7a5c-ff36-5557-84a3-7d4aa0e416b8']
    download_test(["76260cde-ad97-4c5d-b587-4a35bf72346f"], 'download', 'collaboratory', file_name, [202180, 21701],
                  data_dir)
