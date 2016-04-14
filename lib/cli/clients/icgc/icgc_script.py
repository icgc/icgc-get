import subprocess
import logging
import os


def icgc_call(object_id, token, tool_path, output):
    logger = logging.getLogger('__log__')

    os.environ['ACCESSTOKEN'] = token
    call_args = [tool_path, 'download', '--object-id', object_id, '--output-dir', output]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = call.communicate()
    logger.info(output)
    logger.warning(error)


def icgc_manifest_call(manifest, token, tool_path, output):
    logger = logging.getLogger('__log__')
    os.environ['ACCESSTOKEN'] = token
    call_args = {tool_path, '--manifest', manifest,  '--output-dir', output}
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = call.communicate()
    logger.info(output)
    logger.warning(error)
