import subprocess
import logging


def gdc_call(uuid, token, toolpath, output, udt):
    logger = logging.getLogger('__log__')
    if udt:
        call_args = [toolpath, 'download', uuid, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [toolpath, 'download', uuid, '-t', token, '--dir', output]

    logger.info(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)


def gdc_manifest_call(manifest, toolpath, token, output, udt):
    logger = logging.getLogger('__log__')
    if udt:
        call_args = [toolpath, 'download', '-m', manifest, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [toolpath, 'download', '-m', manifest, '-t', token, '--dir', output]

    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, _ = call.communicate()
    logger.info(output)
    logger.warning(_)
