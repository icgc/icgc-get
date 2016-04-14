import subprocess
import logging


def gdc_call(uuid, token, toolpath, output, udt):
    logger = logging.getLogger('__log__')
    if udt == 'off':
        udtflag = ''
    else:
        udtflag = ' -u'
    call_args = [toolpath, uuid, '-t', token, '-d', output, udtflag]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)


def gdc_manifest_call(manifest, toolpath, token, output, udt):
    logger = logging.getLogger('__log__')
    if udt == 'off':
        udtflag = ''
    else:
        udtflag = ' -u'

    call_args = [toolpath, '-m', manifest,  '-t', token, '-d', output, udtflag]
    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)
