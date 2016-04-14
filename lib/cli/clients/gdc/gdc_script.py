from ..run_command import run_command


def gdc_call(uuid, token, tool_path, output, udt):

    if udt:
        call_args = [tool_path, 'download', uuid, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [tool_path, 'download', uuid, '-t', token, '--dir', output]
    run_command(call_args)


def gdc_manifest_call(manifest, tool_path, token, output, udt):

    if udt:
        call_args = [tool_path, 'download', '-m', manifest, '-t', token, '--dir', output, '--udt']
    else:
        call_args = [tool_path, 'download', '-m', manifest, '-t', token, '--dir', output]
    run_command(call_args)

