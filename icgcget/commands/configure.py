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
import click

from icgcget.commands.utils import config_parse
from icgcget.params import PathParam, ReposParam, LogfileParam, GNOS, ALL_REPO_NAMES_STRING

import pkgutil
from jinja2 import Environment, FunctionLoader


class ConfigureDispatcher(object):
    """
    Dispatcher that handles configuration prompts
    """

    """
    Constants
    """
    WELCOME_MSG = \
        'You will receive a series of prompts for all relevant configuration values and access parameters\n' + \
        'Existing configuration values are listed in square brackets.  To keep these values, press Enter. \n' + \
        'To input multiple values for a prompt, separate each value with a space.\n'

    DIR_MSG = 'Enter a directory for downloaded files to be saved to. ' + \
              'icgc-get will attempt to create it if it does not exist.'
    LOG_MSG = 'Enter a location for the process logs to be stored.  Must be in an existing directory.  Optional.'
    REPO_MSG = 'Enter which repositories you want to download from.\n Valid repositories are: {}'\
        .format(ALL_REPO_NAMES_STRING)
    DOCKER_MSG = 'Enter true or false if you wish to use a docker container to download and run all download clients'

    def __init__(self, config_destination, default):
        """
        Init function parses any previous config.yaml files found in the configuration directory
        :param config_destination:
        :param default:
        """
        self.old_config = {}
        self.default_dir = os.path.split(default)[0]
        self.gnos_repos = GNOS.keys()
        if os.path.isfile(config_destination):
            old_config = config_parse(config_destination, default, empty_ok=True)
            if old_config:
                self.old_config = old_config['report']

        self.env = Environment(loader=FunctionLoader(_load_template))
        self.env.trim_blocks = True

    def configure(self, config_destination):
        """
        Series of prompts that gathers info needed for the config.yaml file.
        :param config_destination:
        :return:
        """
        config_directory = os.path.split(config_destination)
        if not os.path.isdir(config_directory[0]):
            raise click.BadOptionUsage('Unable to write to directory {}'.format(config_directory[0]))

        (output, logfile, repos, docker) = self.get_user_config()
        conf_yaml = {'output': output, 'logfile': logfile, 'repos': repos, 'docker': docker}

        if 'aws-virginia' in repos or 'collaboratory' in repos:
            self._icgc_prompt(conf_yaml=conf_yaml)

        gnos_specified = [repo for repo in self.gnos_repos if repo in repos]
        if gnos_specified:
            self._gnos_prompt(gnos_specified=gnos_specified, conf_yaml=conf_yaml)

        if 'ega' in repos:
            self._ega_prompt(conf_yaml=conf_yaml)

        if 'gdc' in repos:
            self._gdc_prompt(conf_yaml=conf_yaml)

        if 'pdc' in repos:
            self._pdc_prompt(conf_yaml=conf_yaml)

        template = self.env.get_template('config.template.yaml')
        config_file = open(config_destination, 'w')
        config_file.write(template.render(conf=conf_yaml))
        os.environ['ICGCGET_CONFIG'] = config_destination
        print 'Configuration file saved to {}'.format(config_file.name)
        config_file.close()

    def get_user_config(self):
        """
        Method responsible for retrieving basic config info from user.
        :return: quadruple of (output, logfile, repos, docker)
        """
        print self.WELCOME_MSG
        # Prompt for output directory
        output = self.prompt('output', 'output', self.DIR_MSG, input_type=PathParam())
        # Prompt for logfile directory
        logfile = self.prompt('logfile', 'logfile', self.LOG_MSG, input_type=LogfileParam())
        # Prompt for repo selection and precedence
        repos = self.prompt('repos', 'repos', self.REPO_MSG, input_type=ReposParam())
        # Prompt for docker
        docker = self.prompt('docker', 'docker', self.DOCKER_MSG, input_type=click.BOOL)

        return output, logfile, repos, docker

    def prompt(self, value_string, value_name, info, input_type=click.STRING, hide=False, skip=False):
        """
        Wraps the click.prompt function. Creates a prompt for the use rbased on passed params.
        :param value_string: Description of value
        :param value_name: Name of value
        :param info: Message for the user
        :param input_type: click.Path
        :param hide: hide input
        :param skip: If true, skips and returns default values
        :return: Returns value from user input
        """
        if value_name in self.old_config and self.old_config[value_name]:
            if value_name == 'repos':
                default = ' '.join(self.old_config[value_name])
            else:
                default = self.old_config[value_name]
        else:
            if value_name == 'logfile':
                default = self.default_dir + '/icgc_get.log'
            else:
                default = ''
        if skip:
            return default
        print '\n' + info
        value = click.prompt(value_string, default=default, hide_input=hide, type=input_type, show_default=not hide)
        if value_name == 'repos' and value == default:  # Default params do not get filtered through input_type.convert
            value = default.split(' ')
        return value

    def handle_error(self, config_destination):
        if click.confirm(click.style('\n\nA fatal error occurred reading/writing the configuration file.\n' +
                         'Delete corrupted configuration?', fg='red', bold=True)):
            try:
                os.remove(config_destination)
                click.echo('Removed bad configuration file: ' + config_destination)
            except Exception:
                click.echo(click.style('Could not remove file, possibly already deleted.', fg='red', bold=True))

    def _icgc_prompt(self, conf_yaml):
        """
        Prompts User for ICGC (AWS & Collab) access tokens
        :param conf_yaml: Dictionary representing yaml config file.
        """
        message = 'Enter the path to your local ICGC storage client installation'
        icgc_path = self.prompt('ICGC path', 'icgc_path', message,
                                input_type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                                skip=conf_yaml['docker'])
        icgc_access = self.prompt('ICGC token', 'icgc_token', 'Enter a valid ICGC access token')
        if icgc_path:
            conf_yaml['icgc'] = {'token': icgc_access, 'path': icgc_path}
        else:
            conf_yaml['icgc'] = {'token': icgc_access}

    def _gnos_prompt(self, gnos_specified, conf_yaml):
        """
        Prompts user for genetorrent access
        :param gnos_specified: Specific gnos repos that were specified.
        :param conf_yaml: Dictionary representing yaml config file.
        """
        gnos_path = self.prompt('gnos path', 'gnos_path', 'Enter the path to your local genetorrent executable',
                                input_type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                                skip=conf_yaml['docker'])
        gnos_keys = {}
        for repo in gnos_specified:
            repo_code = repo.split('-')[-1]
            key = self.prompt(repo.upper() + ' key', 'gnos_key_' + repo_code, 'Enter your ' + repo.upper() + ' key')
            gnos_keys[repo_code] = key
        if gnos_path:
            conf_yaml['gnos'] = {'key': gnos_keys, 'path': gnos_path}
        else:
            conf_yaml['gnos'] = {'key': gnos_keys}

    def _ega_prompt(self, conf_yaml):
        """
        Prompts user for EGA username and password, in addition to path for client.
        :param conf_yaml: Dictionary representing yaml config file.
        """
        ega_path = self.prompt('EGA path', 'ega_path', 'Enter the path to your local EGA download client jar file',
                               input_type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                               skip=conf_yaml['docker'])
        ega_username = self.prompt('EGA username', 'ega_username', 'Enter your EGA username')
        ega_password = self.prompt('EGA password', 'ega_password', 'Enter your EGA password')
        if ega_path:
            conf_yaml['ega'] = {'username': ega_username, 'password': ega_password, 'path': ega_path}
        else:
            conf_yaml['ega'] = {'username': ega_username, 'password': ega_password}

    def _gdc_prompt(self, conf_yaml):
        """
        Prompts user for GDC related auth and path.
        :param conf_yaml: Dictionary representing yaml config file.
        """
        message = "Enter the path to your local GDC download client installation"
        gdc_path = self.prompt('GDC path', 'gdc_path', message,
                               input_type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                               skip=conf_yaml['docker'])

        gdc_access = self.prompt('GDC token', 'gdc_token', 'Enter a valid GDC access token')
        if gdc_path:
            conf_yaml['gdc'] = {'token': gdc_access, 'path': gdc_path}
        else:
            conf_yaml['gdc'] = {'token': gdc_access}

    def _pdc_prompt(self, conf_yaml):
        """
        Prompts user for PDC related auth and path. (AWS FOR PDC)
        :param conf_yaml: Dictionary representing yaml config file.
        """
        message = 'Enter the path to your local AWS-cli installation to access the PDC repository'
        pdc_path = self.prompt('AWS path', 'pdc_path', message,
                               input_type=click.Path(exists=True, dir_okay=False, resolve_path=True),
                               skip=conf_yaml['docker'])
        pdc_key = self.prompt('PDC key', 'pdc_key', 'Enter your PDC s3 key')
        pdc_secret_key = self.prompt('PDC secret key', 'pdc_secret', 'Enter your PDC s3 secret key', hide=True)
        if pdc_path:
            conf_yaml['pdc'] = {'key': pdc_key, 'secret': pdc_secret_key, 'path': pdc_path}
        else:
            conf_yaml['pdc'] = {'key': pdc_key, 'secret': pdc_secret_key}


def _load_template(filename):
    return pkgutil.get_data('templates', filename).decode()
