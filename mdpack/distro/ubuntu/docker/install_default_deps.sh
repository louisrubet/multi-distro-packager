#!/usr/bin/env bash

export TZ=Europe/London
ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

deps=(
   apt-utils
   build-essential
   g++
   cmake
   tree
)

apt update
apt install -y --no-install-recommends apt-utils "${deps[@]}"
