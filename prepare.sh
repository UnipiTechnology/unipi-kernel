#!/bin/bash

set -e

TAG=6.12.66-cip16

create_git_repo()
{
    git init
    git add .
    git commit -m "Init from ${TAG}"
    git am --empty=drop $1/*
}

patch_source()
{
    for p in $1/*.patch; do
        patch -p1 <$p
    done
}

wget "https://git.kernel.org/pub/scm/linux/kernel/git/cip/linux-cip.git/snapshot/linux-cip-${TAG}.tar.gz" -q -O- | tar xz

mv linux-cip-${TAG} linux
(
  cd linux
  if [ "$1" = "build" ]; then
      patch_source ../patches
  else 
      create_git_repo ../patches
  fi
)
