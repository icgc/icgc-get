from ..run_command import run_command


def genetorrent_call(uuid, token, tool_path, output):

    call_args = [tool_path, '-vv', '-c', token, '-d', uuid, '-p', output]
    run_command(call_args)

