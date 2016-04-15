import os
from ..run_command import run_command


def icgc_call(object_id, token, tool_path, output):

    os.environ['ACCESSTOKEN'] = token
    call_args = [tool_path, 'download', '--object-id', object_id, '--output-dir', output]
    run_command(call_args)


def icgc_manifest_call(manifest, token, tool_path, output):

    os.environ['ACCESSTOKEN'] = token
    call_args = {tool_path, '--manifest', manifest,  '--output-dir', output}
    run_command(call_args)
