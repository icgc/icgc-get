#!/usr/bin/python
import subprocess
import random
import string
import logging


def ega_call(id, passfile, udt, downloaddirectory):
    logger = logging.getLogger('__log__')

    lable = id + '_request'
    key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(4))
    if id(4) == 'd':
        downloadtype = ' -rfd '
    else:
        downloadtype = ' -rf '
    requestcall_sequence = ['java', '-jar', 'EgaDemoClient.jar', '-pf', passfile, downloadtype, id, '-re', key,
                            '-label', lable]
    logger.debug(requestcall_sequence)
    requestcall = subprocess.Popen(requestcall_sequence, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if udt == 'off':
        udtflag = ''
    else:
        udtflag = ' -udt'
    output, _ = requestcall.communicate()
    logger.info(output)
    logger.warning(_)
    requestcall.wait()  # some requests may have pending files, need to wait longer than the lenght of the request call

    downloadcall_args = ['java', '-jar', 'EgaDemoClient.jar', '-pf', passfile, '-dr', lable, '-path',
                             downloaddirectory, udtflag]
    logger.debug(downloadcall_args)
    downloadcall = subprocess.Popen(downloadcall_args,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = downloadcall.communicate()
    logger.info(output)
    logger.warning(_)
    downloadcall.wait()  # This process takes hours-need to background the call
    filename = downloaddirectory + ''

    decryptcall_args = ['java', '-jar', 'EgaDemoClient.jar', '-pf', passfile, '-dc', filename, '-dck', key]
    logger.debug(decryptcall_args)
    decryptcall = subprocess.Popen(decryptcall_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = decryptcall.communicate()
    logger.info(output)
    logger.warning(_)
