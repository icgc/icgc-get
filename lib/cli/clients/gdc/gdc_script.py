from ..run_command import run_command



def gdc_call(uuid, token, tool_path, output, udt):

    call_args = [tool_path, 'download', uuid, '-t', token, '--dir', output]
    if udt:
        call_args.append('--udt')
    run_command(call_args)


def gdc_manifest_call(manifest, tool_path, token, output, udt):

    call_args = [tool_path, 'download', manifest, '-t', token, '--dir', output]
    if udt:
        call_args.append('--udt')
    run_command(call_args)

