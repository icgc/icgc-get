#!/bin/bash

repo_mount_path=$1
output_dir=$2
use_local=$3
branch=$4
echo "repo_mount_path = $repo_mount_path"
echo "output_dir = $output_dir"
echo "use_local = $use_local"
echo "branch = $branch"


## Clone only if use_local = 0
url='https://github.com/icgc/icgc-get'
if [[ $use_local -eq 0  ]]; then
    echo "using git clone"
    path=/tmp/icgc-get.$$
    git clone --branch $branch $url $path
    mkdir -p $repo_mount_path
    mv -f $path/* $repo_mount_path
    rm -rf $path
fi

if [ ! -e $repo_mount_path ]; then
	echo "The repo_mount_path \"$repo_mount_path\" DNE"
	exit 1
fi
if [ ! -e $output_dir ]; then
	echo "The output_dir \"$output_dir\" DNE"
	exit 1
fi

echo "repo_mount_path = $repo_mount_path"
echo "output_dir = $output_dir"
cd $repo_mount_path
pip install -r ./requirements.txt
#pyinstaller --clean icgc-get-data.spec
pyinstaller --clean --onefile -n icgc-get --additional-hooks-dir $repo_mount_path/bin $repo_mount_path/icgcget/cli.py
cp dist/icgc-get $output_dir

