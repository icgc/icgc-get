import subprocess
import logging


def icgc_call(objectid, token, repo, output):
    logger = logging.getLogger('__log__')

    call_args = ['icgc-storage-client', 'download', '--object-id', objectid, '-t', token, '--output-dir', output]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)


def icgc_manifest_call(manifest, token, repo, output):
    logger = logging.getLogger('__log__')

    call_args = ['icgc-storage-client download', '--manifest', manifest, '-t', token, '--output-dir', output]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)
