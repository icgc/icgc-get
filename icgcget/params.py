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

import os
import tempfile
import click
import logging

REPOS = {'collaboratory': {'code': 'collaboratory', 'name': 'collab'},
         'aws-virginia': {'code': 'aws-virginia', 'name': 'aws'},
         'ega': {'code': 'ega', 'name': 'european genome association'},
         'gdc': {'code': 'gdc', 'name': 'genomic data commons'},
         'pdc': {'code': 'pdc', 'name': 'bionimbus protected data commons'}}

GNOS = {'pcawg-chicago-icgc': {'code': 'pcawg-chicago-icgc', 'name': 'pcawg-chicago-icgc',
                               'path': "https://gtrepo-osdc-icgc.annailabs.com/"},
        'pcawg-heidelberg': {'code': 'pcawg-heidelberg', 'name': 'pcawg-heidelberg',
                             'path': "https://gtrepo-dkfz.annailabs.com/"},
        'pcawg-london': {'code': 'pcawg-london', 'name': 'pcawg-london', 'path': "https://gtrepo-ebi.annailabs.com/"},
        'pcawg-tokyo': {'code': 'pcawg-tokyo', 'name': 'pcawg-tokyo', 'path': "https://gtrepo-riken.annailabs.com/"},
        'pcawg-seoul': {'code': 'pcawg-seoul', 'name': 'pcawg-seoul', 'path': "https://gtrepo-etri.annailabs.com/"},
        'pcawg-barcelona': {'code': 'pcawg-barcelona', 'name': 'pcawg-barcelona',
                            'path': "https://gtrepo-bsc.annailabs.com/"},
        'pcawg-chicago-tcga': {'code': 'pcawg-chicago-tcga', 'name': 'pcawg-chicago-tcga',
                               'path': "https://gtrepo-osdc-tcga.annailabs.com/"}}

ICGC_REPOS = ['collaboratory', 'aws-virginia'] #TODO: separate ICGC repos out from REPOS dict, and use the keys
ALL_REPO_NAMES = REPOS.keys() + GNOS.keys()
ALL_REPO_NAMES_STRING = ' '.join(ALL_REPO_NAMES)

class LogfileParam(click.ParamType):
    """
    Custom click parameter to verify valid inputs for log files.
    """
    name = 'logfile'

    def convert(self, value, param, ctx):
        """
        Method to check if logfile is an accessible file if it exists or in an accessible directory if it doesn't exist
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        if os.path.isdir(value):
            self.fail('Logfile destination "{}" is a directory'.format(value), param, ctx)
        elif os.path.isfile(value):
            try:
                logfile = open(value, 'a')
                logfile.close()  # need to be able to access the logfile
                return value
            except IOError as ex:
                if ex.errno != 2:
                    self.fail('Unable to write to logfile "{}"'.format(value))
        else:
            try:
                directory, logfile = os.path.split(value)
                if os.access(directory, os.W_OK) and directory != tempfile.gettempdir():
                    return value  # need to check if directory can be written to without actually making a file
                else:
                    self.fail('Logfile cannot be made in selected directory "{}"'.format(directory), param, ctx)
            except ValueError:
                self.fail('Unable to resolve path to logfile "{}"'.format(value), param, ctx)


class RepoParam(click.ParamType):
    """
    Custom click parameter for a single repository.  Used for command line inputs, typically provided in a list
    """
    name = 'repo'

    def convert(self, value, param, ctx):
        """
        Function that verifies that repository name is valid repository name
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        try:
            if value in REPOS.keys() or value in GNOS.keys():
                return value
            else:
                self.fail('Invalid repo "{0}".  Valid repos are: {1}'.format(value, ALL_REPO_NAMES_STRING), param, ctx)
        except ValueError:
            self.fail('{} is not a valid repository'.format(value), param, ctx)


class ReposParam(click.ParamType):
    """
    Custom click parameter for a list of repositories: used in the configure function exclusively due to limitations of
    prompts.
    """
    name = 'repos'

    def convert(self, value, param, ctx):
        """
        Function that ensures every non null value must be a valid repository name.  Null values are stripped later
        :param value:
        :param param:
        :param ctx:
        :return:
        """
        value = value.split(' ')
        repos = []
        for repo in value:
            if repo in ALL_REPO_NAMES:
                repos.append(repo)
            else:
                self.fail('Invalid repository "{0}".  Valid repositories are: {1}'.format(repo, ALL_REPO_NAMES_STRING),
                          param=param, ctx=ctx)
        return repos


class PathParam(click.ParamType):
    """
    Custom parameter to create directory if it doesn't exist.
    """
    name = 'path'

    def convert(self, value, param, ctx):
        """
        Checks for directory, tries to create if it doesn't exist, otherwise fails.
        :param value: value from user
        :param param: param
        :param ctx: context
        :return:
        """

        try:
            if not os.path.exists(value):
                os.makedirs(value)
            elif not os.access(value, os.W_OK):
                self.fail('Directory {} is not writable by icgc-get.'.format(value))
        except OSError as e:
            logging.error(e.message)
            self.fail('Directory {} does not exist and icgc-get was unable to create it.'.format(value))
        except:
            logging.error('Exception thrown during output directory check.')
            raise

        return value

