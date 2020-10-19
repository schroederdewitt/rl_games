#!/bin/bash

echo 'Building Dockerfile with image name rl_games'
nohup docker build --build-arg UID=$UID -t rl_games:ppo . &
