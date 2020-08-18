docker pull tensorflow/tensorflow:devel
git clone https://github.com/tensorflow/tensorflow.git
git checkout r1.15
docker run -it -w /tensorflow -v /users/${USER}/tensorflow:/tensorflow -v $PWD:/mnt \
    -e HOST_PERMS="$(id -u):$(id -g)" --name building_tensorflow_rl_games tensorflow/tensorflow:devel bash

# Inside The container
#wget https://github.com/bazelbuild/bazel/releases/download/0.24.1/bazel-0.24.1-installer-linux-x86_64.sh && \
#chmod +x bazel-0.24.1-installer-linux-x86_64.sh &&
#./bazel-0.24.1-installer-linux-x86_64.sh && \
#rm -f bazel-0.24.1-installer-linux-x86_64.sh && \
#./configure && bazel build --config=opt //tensorflow/tools/pip_package:build_pip_package && \
#./bazel-bin/tensorflow/tools/pip_package/build_pip_package /mnt && \
#chown $HOST_PERMS /mnt/*.whl && pip3 uninstall tensorflow && \
#pip3 install /mnt/*.whl && cd /tmp && python3 -c "import tensorflow as tf; print(tf.__version__)"

docker commit building_tensorflow_rl_games rl_games_cpu
docker kill building_tensorflow_rl_games
docker build -t rl_games_cpu .
