How to build the icgc-get executable
---

## Description
The script `build-icgc-get` is a script created to facilitate the building and running of a docker container that builds the executable.

## Build and run using a git branch
This is useful for building an executable of a branch

```bash
./build-icgc-get -o /path/to/my/output/dir  -b gitrepo_branch --all
```

## Build and run using a local icgc-get repo
This is useful when developing something locally and you want to create an executable

```bash
./build-icgc-get -o /path/to/my/output/dir  -d /path/to/my/local/icgc-get/repo --all
```

## Dry-run
To do a dry run, just append `-n` or `--dry-run` to the end of the `build-icgc-get` command
