import numpy as np
import argparse
import copy
import yaml

import torch

from sacred import Experiment
import numpy as np
import os
import collections
from os.path import dirname, abspath
import pymongo
from sacred import Experiment, SETTINGS
from sacred.observers import FileStorageObserver
from sacred.observers import MongoObserver
from sacred.utils import apply_backspaces_and_linefeeds
from rl_games.utils.logging import get_logger, Logger
SETTINGS.CONFIG.READ_ONLY_CONFIG = False

SETTINGS['CAPTURE_MODE'] = "fd"  # set to "no" if you want to see stdout/stderr in console
logger = get_logger()

ex = Experiment("pymarl")
ex.logger = logger
ex.captured_out_filter = apply_backspaces_and_linefeeds

results_path = os.path.join(dirname(dirname(abspath(__file__))), "results")

mongo_client = None

# if __name__ == '__main__':
#     ap = argparse.ArgumentParser()
#     ap.add_argument("-tf", "--tf", required=False, help="run tensorflow runner", action='store_true')
#     ap.add_argument("-t", "--train", required=False, help="train network", action='store_true')
#     ap.add_argument("-p", "--play", required=False, help="play network", action='store_true')
#     ap.add_argument("-c", "--checkpoint", required=False, help="path to checkpoint")
#     ap.add_argument("-f", "--file", required=True, help="path to config")
#
#     args = vars(ap.parse_args())
#     config_name = args['file']
#     print('Loading config: ', config_name)
#     with open(config_name, 'r') as stream:
#         config = yaml.safe_load(stream)
#
#         if args['tf']:
#             from rl_games.tf14_runner import Runner
#         else:
#             from rl_games.torch_runner import Runner
#
#         runner = Runner(logger)
#         try:
#             runner.load(config)
#         except yaml.YAMLError as exc:
#             print(exc)
#
#     runner.reset()
#     runner.run(args)

# Function to connect to a mongodb and add a Sacred MongoObserver
def setup_mongodb(db_url, db_name):
    client = None
    mongodb_fail = True

    # Try 5 times to connect to the mongodb
    for tries in range(5):
        # First try to connect to the central server. If that doesn't work then just save locally
        maxSevSelDelay = 10000  # Assume 10s maximum server selection delay
        try:
            # Check whether server is accessible
            logger.info("Trying to connect to mongoDB '{}'".format(db_url))
            client = pymongo.MongoClient(db_url, ssl=True, serverSelectionTimeoutMS=maxSevSelDelay)
            client.server_info()
            # If this hasn't raised an exception, we can add the observer
            ex.observers.append(MongoObserver.create(url=db_url, db_name=db_name, ssl=True))  # db_name=db_name,
            logger.info("Added MongoDB observer on {}.".format(db_url))
            mongodb_fail = False
            break
        except pymongo.errors.ServerSelectionTimeoutError:
            logger.warning("Couldn't connect to MongoDB on try {}".format(tries + 1))

    if mongodb_fail:
        logger.error("Couldn't connect to MongoDB after 5 tries!")
        # TODO: Maybe we want to end the script here sometimes?

    return client

@ex.main
def my_main(_run, _config, _log):
    global mongo_client

    import datetime

    # arglist = parse_args()
    # unique_token = "{}__{}".format(arglist.name, datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    # run the framework
    # run(_run, _config, _log, mongo_client, unique_token)

    logger = Logger(_log)

    # configure tensorboard logger
    unique_token = "{}__{}".format(_config["label"], datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    use_tensorboard = False
    if use_tensorboard:
        tb_logs_direc = os.path.join(dirname(dirname(abspath(__file__))), "results", "tb_logs")
        tb_exp_direc = os.path.join(tb_logs_direc, "{}").format(unique_token)
        logger.setup_tb(tb_exp_direc)
    logger.setup_sacred(_run)

    _log.info("Experiment Parameters:")
    import pprint
    experiment_params = pprint.pformat(_config,
                                       indent=4,
                                       width=1)
    _log.info("\n\n" + experiment_params + "\n")
    _config["params"]["config"]["run_id"] = _run._id

    #args = parse_args()
    if _config['use_tf']:
        from rl_games.tf14_runner import Runner
    else:
        from rl_games.torch_runner import Runner

    # START THE TRAINING PROCESS
    runner = Runner(logger)
    runner.load(_config)
    runner.reset()
    # args = vars(arglist)
    runner.run(_config)

    # runner.run(args)

    # train(arglist, logger, _config)
    # arglist = convert(_config)
    # train(arglist)

    # force exit
    os._exit(0)

def _get_config(params, arg_name, subfolder):
    config_name = None
    for _i, _v in enumerate(params):
        if _v.split("=")[0] == arg_name:
            config_name = _v.split("=")[1]
            del params[_i]
            break

    if config_name is not None:
        with open(os.path.join(os.path.dirname(__file__), "rl_games", "configs", subfolder, "{}.yaml".format(config_name)),
                  "r") as f:
            try:
                config_dict = yaml.load(f)
            except yaml.YAMLError as exc:
                assert False, "{}.yaml error: {}".format(config_name, exc)
        return config_dict

def recursive_dict_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            d[k] = recursive_dict_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-tf", "--tf", required=False, help="run tensorflow runner", action='store_true')
    ap.add_argument("-t", "--train", required=False, help="train network", action='store_true')
    ap.add_argument("-p", "--play", required=False, help="play network", action='store_true')
    ap.add_argument("-c", "--checkpoint", required=False, help="path to checkpoint")
    ap.add_argument("-f", "--file", required=True, help="path to config")

    args = vars(ap.parse_args())
    return args


if __name__ == '__main__':
    import os

    import sys
    from copy import deepcopy

    params = deepcopy(sys.argv)

    config_dict = {"train": True,
                   "load_checkpoint": False,
                   "load_path": None}
    file_config = _get_config(params, "--file", "")
    config_dict = recursive_dict_update(config_dict, file_config)

    config_dict["params"]["config"]["cuda_device"] = "cuda:0" if torch.cuda.is_available() else "cpu"
    config_dict["params"]["config"]["use_cuda"] = torch.cuda.is_available()
    config_dict["use_tf"] = "--tf" in params

    # now add all the config to sacred
    ex.add_config(config_dict)

    # Check if we don't want to save to sacred mongodb
    no_mongodb = False

    for _i, _v in enumerate(params):
        if "no-mongo" in _v:
            if "--no-mongo" == _v:
                del params[_i]
                no_mongodb = True
                break

    config_dict = {"train": True}
    db_config_path = "./db_config.private.yaml"
    with open(db_config_path, 'r') as stream:
        config_dict = yaml.safe_load(stream)

    # If there is no url set for the mongodb, we cannot use it
    if not no_mongodb and "db_url" not in config_dict:
        no_mongodb = True
        logger.error("No 'db_url' to use for Sacred MongoDB")

    if not no_mongodb:
        db_url = config_dict["db_url"]
        db_name = config_dict["db_name"]
        mongo_client = setup_mongodb(db_url, db_name)

    # Save to disk by default for sacred, even if we are using the mongodb
    logger.info("Saving to FileStorageObserver in results/sacred.")
    file_obs_path = os.path.join(results_path, "sacred")
    ex.observers.append(FileStorageObserver.create(file_obs_path))

    ex.run_commandline(params)

