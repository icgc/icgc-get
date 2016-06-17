import os
import yaml
import click
from icgcget.commands.utils import config_parse


class ConfigureDispatcher(object):

    def __init__(self, config_destination, default):
        if os.path.isfile(config_destination):
            self.old_config = config_parse(config_destination, default, empty_ok=True)
        else:
            self.old_config = {}

    def configure(self, config_destination):
        try:
            config_file = file(config_destination, 'w')
        except IOError:
            raise click.BadOptionUsage("Unable to write to directory {}".format(config_destination))
        output = self.prompt('output')
        logfile = self.prompt('logfile')
        icgc_path = self.prompt('path', 'icgc')
        icgc_access = self.prompt('access', 'icgc', True)
        cghub_path = self.prompt('path', 'cghub')
        cghub_access = self.prompt('access', 'cghub', True)
        ega_path = self.prompt('path', 'ega')
        ega_username = self.prompt('username', 'ega')
        ega_password = self.prompt('password', 'ega', True)
        gdc_path = self.prompt('path', 'gdc')
        gdc_access = self.prompt('access', 'gdc', True)
        pdc_path = self.prompt('path', 'pdc')
        pdc_key = self.prompt('key', 'pdc', True)
        pdc_secret_key = self.prompt('secret_key', 'pdc', True)
        conf_yaml = {'output': output, 'logfile': logfile,
                     'icgc': {'path': icgc_path, 'access': icgc_access},
                     'cghub': {'path': cghub_path, 'access': cghub_access},
                     'ega': {'path': ega_path, 'username': ega_username, 'password': ega_password},
                    'gdc': {'path': gdc_path, 'access': gdc_access},
                    'pdc': {'path': pdc_path, 'key': pdc_key, 'secret': pdc_secret_key}}

        yaml.dump(conf_yaml, config_file, encoding=None, default_flow_style=False)
        os.environ['ICGCGET_CONFIG'] = output + 'config.yaml'

    def prompt(self, value_name, repo='', hide=False):
        if repo and repo in self.old_config and value_name in self.old_config[repo]:
            default = self.old_config[repo][value_name]
        elif value_name in self.old_config:
            default = self.old_config[value_name]
        else:
            default = ''
        if repo:
            value_name = repo + ' ' + value_name
        return click.prompt(value_name, default=default, hide_input=hide)

