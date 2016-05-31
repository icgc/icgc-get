import abc
import logging
import pickle
import subprocess
import subprocess32
import re


class DownloadClient(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, pickle_path=None):
        self.logger = logging.getLogger('__log__')
        self.jobs = []
        self.session = {}
        self.path = pickle_path
        self.repo = ''

    @abc.abstractmethod
    def download(self, manifest, access, tool_path, output,  processes, udt=None, file_from=None, repo=None,
                 region=None):
        return

    @abc.abstractmethod
    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None, region=None):
        return

    @abc.abstractmethod
    def print_version(self, path, access=None):
        return

    @abc.abstractmethod
    def version_parser(self, output):
        return

    @abc.abstractmethod
    def download_parser(self, output):
        self.logger.info(output)

    def _run_command(self, args, parser, env=None):
        self.logger.debug(args)
        if None in args:
            self.logger.warning("Missing argument in {}".format(args))
            return 1
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as e:
            self.logger.warning(e.output)
            return e.returncode
        except OSError:
            self.logger.warning("Path to download tool does not lead to expected application")
            return 2
        while True:
            output = process.stdout.readline()
            if process.poll() is not None:
                break
            if output:
                parser(output.strip())
        rc = process.poll()
        if rc == 0 and self.session:
            self.session_update('', self.repo)  # clear any running files if exit cleanly
        return rc

    def session_update(self, file_name, repo):
        for fi_id, file_object in self.session[repo].items():
            if file_object['index_filename'] == file_name or file_object['filename'] == file_name:
                file_object['state'] = 'Running'
            elif file_object['state'] == 'Running':  # only one file at a time can be downloaded.
                file_object['state'] = 'Finished'
        pickle.dump(self.session, open(self.path, 'w'))

    def _run_test_command(self, args, env=None):
        if None in args:
            self.logger.warning("Missing argument in {}".format(args))
            return 1
        try:
            subprocess32.check_output(args, stderr=subprocess.STDOUT, env=env, timeout=2)
        except subprocess32.CalledProcessError as e:
            self.logger.info(e.output)
            return e.returncode
        except OSError:
            return 2
        except subprocess32.TimeoutExpired as e:
            invalid_login = re.findall("403 Forbidden", e.output)
            not_found = re.findall("404 Not Found", e.output)
            if invalid_login:
                return 3
            elif not_found:
                return 403
            else:
                return 0
