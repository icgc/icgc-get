#!/bin/bash

if [  -z ${USE_LOCAL+x}  ]; then
    echo "The env variable USE_LOCAL is undefined"
    exit 1
else
    echo "USE_LOCAL = $USE_LOCAL"
fi

if [  -z ${REPO_MOUNT_PATH+x}  ]; then
    echo "The env variable REPO_MOUNT_PATH is undefined"
    exit 1
else
    echo "REPO_MOUNT_PATH = $REPO_MOUNT_PATH"
fi

if [  -z ${OUTPUT_DIR+x}  ]; then
    echo "The env variable OUTPUT_DIR is undefined"
    exit 1
else
    echo "OUTPUT_DIR = $OUTPUT_DIR"
fi


## Clone only if use_local = 0
url='https://github.com/icgc/icgc-get'
if [[ $USE_LOCAL -eq 0  ]]; then
    if [  -z ${GIT_BRANCH+x}  ]; then
        echo "The env variable GIT_BRANCH is undefined"
        exit 1
    else
        echo "GIT_BRANCH = $GIT_BRANCH"
    fi
    echo "using git clone"
    path=/tmp/icgc-get.$$
    git clone --branch $GIT_BRANCH $url $path
    mkdir -p $REPO_MOUNT_PATH
    mv -f $path/* $REPO_MOUNT_PATH
    rm -rf $path
fi

if [ ! -e $REPO_MOUNT_PATH ]; then
	echo "The repo_mount_path \"$REPO_MOUNT_PATH\" DNE"
	exit 1
fi
if [ ! -e $OUTPUT_DIR ]; then
	echo "The output_dir \"$OUTPUT_DIR\" DNE"
	exit 1
fi

cd $REPO_MOUNT_PATH
pip install -r ./requirements.txt
#pyinstaller --clean icgc-get-data.spec
pyinstaller --clean --onefile -n icgc-get --additional-hooks-dir $REPO_MOUNT_PATH/bin $REPO_MOUNT_PATH/icgcget/cli.py
cp dist/icgc-get $OUTPUT_DIR

