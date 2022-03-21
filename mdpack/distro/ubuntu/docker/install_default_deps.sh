#!/usr/bin/env bash

#export TZ=Europe/London
#ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

apt-get update
apt-get install -y --no-install-recommends build-essential g++ cmake tree
