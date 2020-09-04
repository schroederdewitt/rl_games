#!/bin/bash
docker login
docker pull tarun018/rl_games_cpu

echo 'Building Dockerfile with image name rl_games_cpu'
docker build -t rl_games_cpu .
