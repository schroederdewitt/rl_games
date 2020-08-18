FROM rl_games_cpu
# FROM ubuntu:16.04
MAINTAINER Tarun Gupta

# Ubuntu Packages
RUN apt-get update -y && apt-get install software-properties-common -y && \
    add-apt-repository -y multiverse && apt-get update -y && apt-get upgrade -y && \
    apt-get install -y apt-utils nano vim man build-essential wget sudo && \
    rm -rf /var/lib/apt/lists/*

# Install curl and other dependencies
RUN apt-get update -y && apt-get install -y curl libssl-dev openssl libopenblas-dev \
    libhdf5-dev hdf5-helpers hdf5-tools libhdf5-serial-dev libprotobuf-dev protobuf-compiler git \
    libsm6 libxext6 libxrender-dev unzip curl wget zip rsync

#Install python3 pip3
RUN apt-get update
RUN pip3 install --upgrade pip
RUN pip3 install scikit-build cmake
RUN pip3 install scipy pyyaml matplotlib imageio pygame tensorboard-logger ruamel.base \
ryd wheel six numpy mock keras_applications keras_preprocessing

RUN pip3 install jsonpickle setuptools sacred pymongo gym ray==0.6.6

RUN pip3 install tensorboardX==1.6 tensorflow-probability==0.7.0 opencv-python==4.1.0.25 \
 gym-super-mario-bros==7.1.6 pybullet==2.5.0

RUN pip3 install torch==1.5.0

#
### -- SMAC
ENV smac_ver 1
RUN pip3 install git+https://github.com/oxwhirl/smac.git
ENV SC2PATH /pymarl/3rdparty/StarCraftII
#
WORKDIR /pymarl
