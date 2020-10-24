#!/bin/bash
HASH=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 4 | head -n 1)
GPU=$1
name=${USER}_rl_games_GPU_${GPU}_${HASH}

echo "Launching container named '${name}'"
# Launches a docker container using our image, and runs the provided command

docker run \
    --cpus 11.0 \
    --name $name \
    --user $(id -u) \
    -v `pwd`:/pymarl \
    -v `pwd`/results:/results \
    -v `pwd`/runs:/runs \
    -t tarun018/rl_games_cpu \
    ${@:2}
