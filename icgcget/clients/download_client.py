import abc
import logging
import subprocess
import subprocess32
import re


class DownloadClient(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        logger = logging.getLogger('__log__')

    @abc.abstractmethod
    def download(self, manifest, access, tool_path, output,  processes, udt=None, file_from=None, repo=None):
        return

    @abc.abstractmethod
    def access_check(self, access, uuids=None, path=None, repo=None, output=None, api_url=None):
        return

    def _run_command(self, args, env=None):
        self.logger.info(args)
        if None in args:
            logger.warning("Missing argument in {}".format(args))
            return 1
        try:
            process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        except subprocess.CalledProcessError as e:
            self.logger.warning(e.output)
            return e.returncode
        except OSError:
            logger.warning("Path to download tool does not lead to expected application")
            return 2
        while True:
            output = process.stdout.readline()
            if process.poll() is not None:
                break
            if output:
                self.logger.info(output.strip())
        rc = process.poll()
        return rc

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
