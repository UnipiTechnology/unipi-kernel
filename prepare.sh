#!/bin/bash

set -e

. ./upstream.env

create_git_repo()
{
  git clone --depth 1 --branch "v${TAG}" "${CIP_REPO}" linux
  cd linux
  git am --empty=drop ../patches/*
}

patch_source()
{
  wget "${CIP_REPO}/snapshot/linux-cip-${TAG}.tar.gz" -q -O- | tar xz
  mv linux-cip-${TAG} linux
  cd linux
    for p in ../patches/*.patch; do
      patch -p1 <$p
    done
}

# Fetch cip-kernel-sec for VEX generation (needed at build time).
# Shallow clone keeps it small (~80 MB).
rm -rf cip-kernel-sec
git clone --depth=1 "${ADVISORIES}" cip-kernel-sec

(
  if [ "$1" = "build" ]; then
    patch_source
  else
    create_git_repo
  fi

  if [ -n "${CI_COMMIT_TAG}" ]; then
    LOCALVER=$(echo ${CI_COMMIT_TAG} | awk -F. '{print "+" $NF}')
  elif [ -n "${CI_COMMIT_SHORT_SHA}" ]; then
    LOCALVER="-g${CI_COMMIT_SHORT_SHA}"
  fi

  if [ -n "${LOCALVER}" ]; then
    sed  "1s/\$/$LOCALVER/" -i localversion-cip
  fi
)
