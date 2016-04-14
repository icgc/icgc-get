import subprocess
import logging
import os


def icgc_call(objectid, token, toolpath, output):
    logger = logging.getLogger('__log__')

    os.environ['ACCESSTOKEN'] = token
    call_args = [toolpath, 'download', '--object-id', objectid, '--output-dir', output]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)


def icgc_manifest_call(manifest, token, toolpath, output):
    logger = logging.getLogger('__log__')
    os.environ['ACCESSTOKEN'] = token
    call_args = {toolpath, '--manifest', manifest,  '--output-dir', output}
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)
