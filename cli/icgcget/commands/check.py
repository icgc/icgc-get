import logging
import pickle
from icgcget.clients.utils import convert_size


def check_download(pickle_path):
    logger = logging.getLogger('__log__')
    status = pickle.load(open(pickle_path, 'r+'))
    for repo in status:
        finished = 0
        not_started = 0
        for fi_id in status[repo]:
            if status[repo][fi_id]['state'] == 'finished':
                finished += status[repo][fi_id]['size']
            elif status[repo][fi_id]['state'] == 'not_started':
                not_started += status[repo][fi_id]['size']
        finished_size = convert_size(finished)
        finished_size = finished_size[0] + finished_size[1]
        not_started_size = convert_size(not_started)
        not_started_size = not_started_size[0] + not_started_size[1]
        logger.warning('{0} files to download, {1} files downloaded from {2}'.format(finished, not_started, repo))
        logger.warning('{0} to download, {1} downloaded from {2}'.format(finished_size, not_started_size, repo))
