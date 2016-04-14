import subprocess
import logging


def gdc_call(uuid, token, tool_path, output, udt):
    logger = logging.getLogger('__log__')
    if udt:
        call_args = [tool_path, 'download', uuid, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [tool_path, 'download', uuid, '-t', token, '--dir', output]

    logger.info(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = call.communicate()
    logger.info(output)
    logger.warning(error)


def gdc_manifest_call(manifest, tool_path, token, output, udt):
    logger = logging.getLogger('__log__')
    if udt:
        call_args = [tool_path, 'download', '-m', manifest, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [tool_path, 'download', '-m', manifest, '-t', token, '--dir', output]

    logger.debug(call_args)
    call = subprocess.Popen(call_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = call.communicate()
    logger.info(output)
    logger.warning(error)
