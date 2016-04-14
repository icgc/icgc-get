#!/usr/bin/python
import subprocess
from random import SystemRandom
from string import ascii_uppercase, digits
import logging


def ega_call(object_id, pass_file, tool_path, udt, download_dir):
    logger = logging.getLogger('__log__')

    label = object_id + '_request'
    key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))
    if object_id[4] == 'd':
        download_type = '-rfd'
    else:
        download_type = '-rf'
    request_call_args = ['java', '-jar', tool_path, '-pf', pass_file, download_type, id, '-re', key,
                         '-label', label]
    logger.debug(request_call_args)
    request_call = subprocess.Popen(request_call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = request_call.communicate()
    logger.info(output)
    logger.warning(error)

    if udt:
        download_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dr', label, '-path',
                              download_dir, '-udt']
    else:
        download_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dr', label, '-path',
                              download_dir]

    request_call.wait()  # some requests may have pending files, need to wait longer than the length of the request call

    logger.debug(download_call_args)
    download_call = subprocess.Popen(download_call_args,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = download_call.communicate()
    logger.info(output)
    logger.warning(error)
    download_call.wait()  # This process takes hours-need to background the call
    filename = download_dir + ''

    decrypt_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dc', filename, '-dck', key]
    logger.debug(decrypt_call_args)
    decrypt_call = subprocess.Popen(decrypt_call_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, error = decrypt_call.communicate()
    logger.info(output)
    logger.warning(error)
