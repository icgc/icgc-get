#!/usr/bin/python
from ..run_command import run_command
from random import SystemRandom
from string import ascii_uppercase, digits


def ega_call(object_id, pass_file, tool_path, udt, download_dir):

    label = object_id + '_request'
    key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))
    if object_id[4] == 'd':
        download_type = '-rfd'
    else:
        download_type = '-rf'
    request_call_args = ['java', '-jar', tool_path, '-pf', pass_file, download_type, id, '-re', key,
                         '-label', label]
    run_command(request_call_args)


    if udt:
        download_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dr', label, '-path',
                              download_dir, '-udt']
    else:
        download_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dr', label, '-path',
                              download_dir]
    run_command(download_call_args)

    filename = download_dir + ''
    decrypt_call_args = ['java', '-jar', tool_path, '-pf', pass_file, '-dc', filename, '-dck', key]
    run_command(decrypt_call_args)
