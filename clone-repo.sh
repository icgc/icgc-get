#!/bin/bash

branch=$1
use_local=$2
repo_mount_path=$3
url='https://github.com/icgc/icgc-get'
if [[ $use_local -eq 0 ]]; then
	echo "using git clone"
	git clone --branch $branch $url $repo_mount_path
fi
	
