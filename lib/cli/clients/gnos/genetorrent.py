import subprocess
import logging


def genetorrent_call(uuid, token, toolpath, output):
    logger = logging.getLogger('__log__')

    call_args = [toolpath, '-vv', '-c', token, '-d', uuid, '-p', output]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)
