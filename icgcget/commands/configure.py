import os
import yaml
import click
from icgcget.commands.utils import config_parse


class ConfigureDispatcher(object):

    def __init__(self, config_destination, default):
        self.old_config = {}
        if os.path.isfile(config_destination):
            old_config = config_parse(config_destination, default, empty_ok=True)
            if old_config:
                self.old_config = old_config['report']

    def configure(self, config_destination, paths=True):
        config_directory = os.path.split(config_destination)
        if not os.path.isdir(config_directory[0]):
            raise click.BadOptionUsage("Unable to write to directory {}".format(config_destination))
        output = self.prompt('output', input_type=click.Path(exists=True, writable=True, file_okay=False,
                                                             resolve_path=True))
        logfile = self.prompt('logfile')
        repos = self.prompt('repos')
        try:
            repos = repos.split(' ')
        except AttributeError:
            repos = repos
        icgc_path = self.prompt('icgc_path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
        icgc_access = self.prompt('icgc_token', hide=True)
        cghub_path = self.prompt('cghub_path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
        cghub_access = self.prompt('cghub_key', hide=True)
        ega_path = self.prompt('ega_path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
        ega_username = self.prompt('ega_username')
        ega_password = self.prompt('ega_password', hide=True)
        gdc_path = self.prompt('gdc_path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
        gdc_access = self.prompt('gdc_token', hide=True)
        pdc_path = self.prompt('pdc_path', input_type=click.Path(exists=True, dir_okay=False, resolve_path=True))
        pdc_key = self.prompt('pdc_key')
        pdc_secret_key = self.prompt('pdc_secret_key', hide=True)
        conf_yaml = {'output': output, 'logfile': logfile, 'repos': repos,
                     'icgc': {'path': icgc_path, 'token': icgc_access},
                     'cghub': {'path': cghub_path, 'key': cghub_access},
                     'ega': {'path': ega_path, 'username': ega_username, 'password': ega_password},
                     'gdc': {'path': gdc_path, 'token': gdc_access},
                     'pdc': {'path': pdc_path, 'key': pdc_key, 'secret': pdc_secret_key}}

        config_file = open(config_destination, 'w')
        yaml.dump(conf_yaml, config_file, encoding=None, default_flow_style=False)
        os.environ['ICGCGET_CONFIG'] = config_destination

    def prompt(self, value_name, input_type=click.STRING, hide=False):
        default = None
        if value_name in self.old_config:
            default = self.old_config[value_name]
        if not default:
            default = ''
        value = click.prompt(value_name, default=default, hide_input=hide, type=input_type, show_default=not hide)
        if value == '':
            value = None
        return value
