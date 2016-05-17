import abc
import logging


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
