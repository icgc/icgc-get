#!/usr/bin/python
from ..run_command import run_command
from random import SystemRandom
from string import ascii_uppercase, digits
import os
import fnmatch


def ega_call(object_id, pass_file, tool_path, udt, download_dir):

    label = object_id + '_request'
    key = ''.join(SystemRandom().choice(ascii_uppercase + digits) for _ in range(4))  # Make randomized decryption key
    args = ['java', '-jar', tool_path, '-pf', pass_file]  # Parameters needed for all ega client commands

    request_call_args = args
    if object_id[3] == 'D':
        request_call_args.append('-rfd')
    else:
        request_call_args.append('-rf')
    request_call_args.extend([object_id, '-re', key, '-label', label])
    run_command(request_call_args)
    download_call_args = args
    download_call_args.extend(['-dr', label, '-path', download_dir])
    if udt:
        download_call_args.append('-udt')
    run_command(download_call_args)
    decrypt_call_args = args
    decrypt_call_args.append('-dc')
    for file in os.listdir(download_dir):  # file names cannot be dynamically predicted from dataset names
        if fnmatch.fnmatch(file, '*.cip'):  # Tool attempts to decrypt all encrypted files in downloads.
            decrypt_call_args.append(download_dir + '/' + file)

    decrypt_call_args.extend(['-dck', key])
    run_command(decrypt_call_args)
