#!/bin/bash
HASH=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 4 | head -n 1)
GPU=$1
name=${USER}_rl_games_GPU_${GPU}_${HASH}

echo "Launching container named '${name}' on GPU '${GPU}'"
# Launches a docker container using our image, and runs the provided command

if hash nvidia-docker 2>/dev/null; then
  cmd=nvidia-docker
else
  cmd=docker
fi

#$(id -u) \
NV_GPU="$GPU" ${cmd} run -i \
    --name $name \
    --user $(id -u) \
    -v `pwd`:/home/minsun/pymarl \
    rl_games:ppo \
    ${@:2}
