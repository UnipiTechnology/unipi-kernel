#!/bin/bash

set -e

. ./upstream.env

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

wget "${CIP_REPO}/snapshot/linux-cip-${TAG}.tar.gz" -q -O- | tar xz

# Fetch cip-kernel-sec for VEX generation (needed at build time).
# Shallow clone keeps it small (~80 MB).
git clone --depth=1 "${ADVISORIES}" cip-kernel-sec

mv linux-cip-${TAG} linux
(
  cd linux

  if [ -n "${CI_COMMIT_TAG}" ]; then
    LOCALVER=$(echo ${CI_COMMIT_TAG} | awk -F. '{print "+" $NF}')
  elif [ -n "${CI_COMMIT_SHORT_SHA}" ]; then
    LOCALVER="-g${CI_COMMIT_SHORT_SHA}"
  fi

  if [ -n "${LOCALVER}" ]; then
    sed  "1s/\$/$LOCALVER/" -i localversion-cip
  fi

  if [ "$1" = "build" ]; then
      patch_source ../patches
  else
      create_git_repo ../patches
  fi
)
