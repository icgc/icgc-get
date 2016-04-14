#!/usr/bin/python
import subprocess
import random
import string
import logging


def ega_call(id, passfile, toolpath, udt, downloaddirectory):
    logger = logging.getLogger('__log__')

    lable = id + '_request'
    key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(4))
    if id[4] == 'd':
        downloadtype = '-rfd'
    else:
        downloadtype = '-rf'
    requestcall_args = ['java', '-jar', toolpath, '-pf', passfile, downloadtype, id, '-re', key,
                        '-label', lable]
    logger.debug(requestcall_args)
    requestcall = subprocess.Popen(requestcall_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = requestcall.communicate()
    logger.info(output)
    logger.warning(_)

    if udt:
        downloadcall_args = ['java', '-jar', toolpath, '-pf', passfile, '-dr', lable, '-path',
                             downloaddirectory, '-udt']
    else:
        downloadcall_args = ['java', '-jar', toolpath, '-pf', passfile, '-dr', lable, '-path',
                             downloaddirectory]

    requestcall.wait()  # some requests may have pending files, need to wait longer than the lenght of the request call

    logger.debug(downloadcall_args)
    downloadcall = subprocess.Popen(downloadcall_args,  stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = downloadcall.communicate()
    logger.info(output)
    logger.warning(_)
    downloadcall.wait()  # This process takes hours-need to background the call
    filename = downloaddirectory + ''

    decryptcall_args = ['java', '-jar', toolpath, '-pf', passfile, '-dc', filename, '-dck', key]
    logger.debug(decryptcall_args)
    decryptcall = subprocess.Popen(decryptcall_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output, _ = decryptcall.communicate()
    logger.info(output)
    logger.warning(_)
