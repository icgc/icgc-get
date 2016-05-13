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
import subprocess
import subprocess32
import re


def run_command(args, env=None):
    logger = logging.getLogger("__log__")
    logger.info(args)
    if None in args:
        logger.warning("Missing argument in {}".format(args))
        return 1
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    except subprocess.CalledProcessError as e:
        logger.warning(e.output)
        return e.returncode
    except OSError:
        logger.warning("Path to download tool does not lead to expected application")
        return 2
    while True:
        output = process.stdout.readline()
        if process.poll() is not None:
            break
        if output:
            logger.info(output.strip())
    rc = process.poll()
    return rc


def run_test_command(args, env=None):
    logger = logging.getLogger("__log__")
    if None in args:
        logger.warning("Missing argument in {}".format(args))
        return 1
    try:
        subprocess32.check_output(args, stderr=subprocess.STDOUT, env=env, timeout=2)
    except subprocess32.CalledProcessError as e:
        logger.info(e.output)
        return e.returncode
    except OSError:
        logger.warning("Path to download tool does not lead to expected application")
        return 2
    except subprocess32.TimeoutExpired as e:
        error = re.findall("403 Forbidden", e.output)
        if error:
            return 3
        else:
            return 0
