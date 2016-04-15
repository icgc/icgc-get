import logging
import subprocess


def run_command(args):

    logger = logging.getLogger("__log__")
    logger.info(args)
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            logger.info(output.strip())
    rc = process.poll()
    return rc
