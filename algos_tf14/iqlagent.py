import tensorflow as tf
import algos_tf14.models
from common import tr_helpers, experience, env_configurations
import numpy as np
import collections
import time
from collections import deque
from tensorboardX import SummaryWriter
from datetime import datetime
from algos_tf14.tensorflow_utils import TensorFlowVariables
from common.categorical import CategoricalQ
import tensorflow_probability as tfp
import common.vecenv as vecenv
import copy


class IQLAgent:
    def __init__(self, sess, base_name, observation_space, action_space, config, logger, central_state_space=None):
        observation_shape = observation_space.shape
        actions_num = action_space.n
        self.config = config
        self.is_adaptive_lr = config['lr_schedule'] == 'adaptive'
        self.is_polynom_decay_lr = config['lr_schedule'] == 'polynom_decay'
        self.is_exp_decay_lr = config['lr_schedule'] == 'exp_decay'
        self.lr_multiplier = tf.constant(1, shape=(), dtype=tf.float32)
        self.learning_rate_ph = tf.placeholder('float32', (), name='lr_ph')
        self.games_to_track = tr_helpers.get_or_default(config, 'games_to_track', 100)
        self.max_epochs = tr_helpers.get_or_default(self.config, 'max_epochs', 1e6)

        self.games_to_log = self.config.get('games_to_track', 100)
        self.game_rewards = deque([], maxlen=self.games_to_track)
        self.game_lengths = deque([], maxlen=self.games_to_track)
        self.game_scores = deque([], maxlen=self.games_to_log)

        self.epoch_num = tf.Variable(tf.constant(0, shape=(), dtype=tf.float32), trainable=False)
        self.update_epoch_op = self.epoch_num.assign(self.epoch_num + 1)
        self.current_lr = self.learning_rate_ph

        if self.is_adaptive_lr:
            self.lr_threshold = config['lr_threshold']
        if self.is_polynom_decay_lr:
            self.lr_multiplier = tf.train.polynomial_decay(1.0, global_step=self.epoch_num, decay_steps=self.max_epochs,
                                                           end_learning_rate=0.001,
                                                           power=tr_helpers.get_or_default(config, 'decay_power', 1.0))
        if self.is_exp_decay_lr:
            self.lr_multiplier = tf.train.exponential_decay(1.0, global_step=self.epoch_num,
                                                            decay_steps=self.max_epochs,
                                                            decay_rate=config['decay_rate'])

        self.env_name = config['env_name']
        self.network = config['network']
        self.batch_size = self.config['batch_size']

        self.obs_shape = observation_shape
        self.actions_num = actions_num
        self.writer = SummaryWriter('runs/' + config['name'] + datetime.now().strftime("%d, %H:%M:%S"))
        self.epsilon = self.config['epsilon']
        self.rewards_shaper = self.config['reward_shaper']
        self.epsilon_processor = tr_helpers.LinearValueProcessor(self.config['epsilon'], self.config['min_epsilon'],
                                                                 self.config['epsilon_decay_frames'])
        self.beta_processor = tr_helpers.LinearValueProcessor(self.config['priority_beta'], self.config['max_beta'],
                                                              self.config['beta_decay_frames'])

        self.num_actors = config['num_actors']
        self.env_config = self.config.get('env_config', {})
        self.vec_env = vecenv.create_vec_env(self.env_name, self.num_actors, **self.env_config)
        # if self.env_name:
        #     self.env_config = config.get('env_config', {})
        #     self.env = env_configurations.configurations[self.env_name]['env_creator'](**self.env_config)
        self.sess = sess
        self.steps_num = self.config['steps_num']

        self.obs_act_rew = deque([], maxlen=self.steps_num)

        self.is_prioritized = config['replay_buffer_type'] != 'normal'
        self.atoms_num = self.config['atoms_num']
        assert self.atoms_num == 1

        if central_state_space is not None:
            self.state_shape = central_state_space.shape
        else:
            raise NotImplementedError("central_state_space input to IQL is NONE!")
        self.n_agents = self.vec_env.get_number_of_agents()
        self.n_actions = self.vec_env.get_number_of_actions()

        if not self.is_prioritized:
            self.exp_buffer = experience.ReplayBuffer(config['replay_buffer_size'], observation_space, self.n_agents)
        else:
            raise NotImplementedError("Not implemented! PrioritizedReplayBuffer with CentralState")
            # self.exp_buffer = experience.PrioritizedReplayBufferCentralState(config['replay_buffer_size'], config['priority_alpha'])
            # self.sample_weights_ph = tf.placeholder(tf.float32, shape=[None, 1], name='sample_weights')

        self.batch_size_ph = tf.compat.v1.placeholder(tf.int32, name='batch_size_ph')
        self.batch_size_ph = tf.compat.v1.placeholder(tf.int32, name='batch_size_ph')
        self.obs_ph = tf.compat.v1.placeholder(observation_space.dtype, shape=(None,) + self.obs_shape, name='obs_ph')
        self.state_ph = tf.compat.v1.placeholder(observation_space.dtype, shape=(None,) + self.state_shape, name='state_ph')
        self.actions_ph = tf.compat.v1.placeholder(tf.int32, shape=[None, 1], name='actions_ph')
        self.rewards_ph = tf.compat.v1.placeholder(tf.float32, shape=[None, self.n_agents, 1], name='rewards_ph')
        self.next_obs_ph = tf.compat.v1.placeholder(observation_space.dtype, shape=(None,) + self.obs_shape, name='next_obs_ph')
        self.is_done_ph = tf.compat.v1.placeholder(tf.float32, shape=[None, self.n_agents, 1], name='is_done_ph')
        self.is_not_done = 1 - self.is_done_ph
        self.name = base_name

        self.gamma = self.config['gamma']
        self.gamma_step = self.gamma ** self.steps_num
        self.grad_norm = config['grad_norm']
        self.input_obs = self.obs_ph
        self.input_next_obs = self.next_obs_ph
        if observation_space.dtype == np.uint8:
            print('scaling obs')
            self.input_obs = tf.to_float(self.input_obs) / 255.0
            self.input_next_obs = tf.to_float(self.input_next_obs) / 255.0
        self.setup_qvalues(actions_num)

        self.reg_loss = tf.compat.v1.losses.get_regularization_loss()
        self.td_loss_mean += self.reg_loss
        self.learning_rate = self.config['learning_rate']
        self.train_step = tf.compat.v1.train.AdamOptimizer(
            self.learning_rate * self.lr_multiplier)  # .minimize(self.td_loss_mean, var_list=self.weights)
        grads = tf.gradients(self.td_loss_mean, self.weights)
        if self.config['truncate_grads']:
            grads, _ = tf.clip_by_global_norm(grads, self.grad_norm)
        grads = list(zip(grads, self.weights))
        self.train_op = self.train_step.apply_gradients(grads)

        self.saver = tf.compat.v1.train.Saver()
        self.assigns_op = [tf.compat.v1.assign(w_target, w_self, validate_shape=True) for w_self, w_target in
                           zip(self.weights, self.target_weights)]
        self.variables = TensorFlowVariables(self.qvalues, self.sess)
        if self.env_name:
            sess.run(tf.compat.v1.global_variables_initializer())
        self._reset()

        self.logger = logger
        self.num_env_steps_train = 0

    def get_weights(self):
        return self.variables.get_flat()

    def set_weights(self, weights):
        return self.variables.set_flat(weights)

    def update_epoch(self):
        return self.sess.run([self.update_epoch_op])[0]

    def setup_qvalues(self, actions_num):
        config = {
            'input_obs': self.input_obs,
            'input_next_obs': self.input_next_obs,
            'actions_num': actions_num,
            'is_double': self.config['is_double'],
            'actions_ph': self.actions_ph,
            'batch_size_ph': self.batch_size_ph,
            'n_agents': self.n_agents
        }

        # (bs, n_agents, n_actions), (bs, n_agents, 1), (bs, n_agents, 1)
        self.qvalues, self.current_action_qvalues, self.target_action_qvalues = self.network(config)

        self.weights = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='agent')
        self.target_weights = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope='target')

        self.reference_qvalues = self.rewards_ph + self.gamma_step * self.is_not_done * self.target_action_qvalues

        if self.is_prioritized:
            # we need to return l1 loss to update priority buffer
            self.abs_errors = tf.abs(self.current_action_qvalues - self.reference_qvalues) + 1e-5
            # the same as multiply gradients later (other way is used in different examples over internet) 
            self.td_loss = tf.losses.huber_loss(self.current_action_qvalues, self.reference_qvalues,
                                                reduction=tf.losses.Reduction.NONE) * self.sample_weights_ph
            self.td_loss_mean = tf.reduce_mean(self.td_loss)
        else:
            self.td_loss_mean = tf.losses.huber_loss(self.current_action_qvalues, self.reference_qvalues,
                                                     reduction=tf.losses.Reduction.MEAN)

    def save(self, fn):
        self.saver.save(self.sess, fn)

    def restore(self, fn):
        self.saver.restore(self.sess, fn)

    def _reset(self):
        self.obs_act_rew.clear()

        # current_obs: num_actors * n_agents, obs_shape
        self.current_obs = self.vec_env.reset()

        self.total_reward = np.array([0.0] * self.num_actors)
        self.total_shaped_reward = np.array([0.0] * self.num_actors)
        self.step_count = np.array([0] * self.num_actors)
        self.is_done = np.array([False] * self.num_actors)

    def get_action(self, obs, avail_acts, epsilon=0.0):
        if np.random.random() < epsilon:
            action = tfp.distributions.Categorical(probs=avail_acts.astype(float)).sample().eval(session=self.sess)
        else:
            # qvals: (n_actors * n_agents, num_actions)
            qvals = self.get_qvalues(obs)
            # (n_actors * n_agents, num_actions)
            qvals[avail_acts == False] = -9999999
            # (n_actors * n_agents)
            action = np.argmax(qvals, axis=1)
        return action

    def get_qvalues(self, obs):
        return self.sess.run(self.qvalues, {self.obs_ph: obs, self.batch_size_ph: self.num_actors})

    def play_steps(self, steps, epsilon=0.0):
        done_reward = [None] * self.num_actors
        done_shaped_reward = [None] * self.num_actors
        done_steps = [None] * self.num_actors
        done_info = [None] * self.num_actors
        steps_rewards = np.array([0.0] * self.num_actors)
        cur_gamma = 1.0
        cur_obs_act_rew_len = len(self.obs_act_rew)

        play_step_t = time.time()

        # always break after one
        while True:
            if cur_obs_act_rew_len > 0:
                obs = self.obs_act_rew[-1][0]
            else:
                obs = self.current_obs
            # obs: (n_actors * n_agents, obs_shape)
            obs = np.reshape(obs, ((self.num_actors * self.n_agents,) + self.obs_shape))
            # state: num_actors * n_agents, state_shape
            # state = self.vec_env.get_states()

            self.writer.add_scalar('play_steps/1', time.time() - play_step_t, self.num_env_steps_train)
            play_step_t = time.time()

            # (n_actors * n_agents,)
            action = self.get_action(obs, self.vec_env.get_action_masks(), epsilon)
            # (n_actors * n_agents,)
            action = np.squeeze(action)

            self.writer.add_scalar('play_steps/2', time.time() - play_step_t, self.num_env_steps_train)
            play_step_t = time.time()

            # new_obs: (n_actors * n_agents, obs_shape)
            # reward: (n_actors * n_agents,)
            # is_done: (n_actors * n_agents,)
            new_obs, reward, is_done, info = self.vec_env.step(action)
            # reward = reward * (1 - is_done)

            self.writer.add_scalar('play_steps/3', time.time() - play_step_t, self.num_env_steps_train)
            play_step_t = time.time()

            self.num_env_steps_train += self.num_actors

            # reward: (n_actors, n_agents,)
            # is_done: (n_actors, n_agents,)
            # state: (n_actors, n_agents, state_shape)
            new_obs = np.reshape(new_obs, ((self.num_actors, self.n_agents,) + self.obs_shape))
            reward = np.reshape(reward, (self.num_actors, self.n_agents,))
            action = np.reshape(action, (self.num_actors, self.n_agents,))
            is_done = np.reshape(is_done, (self.num_actors, self.n_agents,))
            # state = np.reshape(state, ((self.num_actors, self.n_agents,) + self.state_shape))

            # reward: (n_actors,)
            # is_done: (n_actors,)
            # state: (n_actors, n_agents, state_shape)
            # Same reward, done for all agents
            reward = reward[:, 0]
            is_done = is_done[:, 0]
            # state = state[:, 0]

            self.total_reward += reward * (1.0 - self.is_done)
            shaped_reward = self.rewards_shaper(reward)
            self.total_shaped_reward += shaped_reward * (1.0 - self.is_done)
            self.obs_act_rew.append([new_obs, action, shaped_reward, copy.deepcopy(self.is_done)])
            # for l in range(len(self.obs_act_rew)):
            #     print("self.obs_act_rew: {}: {}: {}".format(l, self.obs_act_rew[l][2], self.obs_act_rew[l][4]))
            self.step_count += 1 * (1 - self.is_done)
            self.is_done[is_done == True] = True

            # print("self.step_count: {}".format(self.step_count))
            # print("self.is_done: {}".format(self.is_done))
            # print("action: {}".format(action))
            # print("is_done: {}".format(is_done))
            # print("reward: {}".format(reward))
            # print("shaped_reward: {}".format(shaped_reward))
            # print("total_reward: {}".format(self.total_reward))
            # print("total_shaped_reward: {}".format(self.total_shaped_reward))
            # print("obs: {}".format(obs.shape))
            # print("state: {}".format(state.shape))
            # print("action: {}".format(action.shape))
            # print("is_done: {}".format(is_done.shape))
            # print("reward: {}".format(reward.shape))

            if len(self.obs_act_rew) < steps:
                break

            for i in range(steps):
                sreward = self.obs_act_rew[i][2] * (1.0 - self.obs_act_rew[i][3])
                steps_rewards += sreward * cur_gamma
                cur_gamma = cur_gamma * self.gamma

            next_obs, current_action, _, done_info_ = self.obs_act_rew[0]
            self.current_obs = np.reshape(self.current_obs, ((self.num_actors, self.n_agents,) + self.obs_shape))
            for _ in range(self.num_actors):
                if not done_info_[_]:
                    self.exp_buffer.add(self.current_obs[_], current_action[_],
                                        steps_rewards[_], new_obs[_], copy.deepcopy(self.is_done[_]))
            # print(len(self.exp_buffer))
            self.current_obs = next_obs

            self.writer.add_scalar('play_steps/4', time.time() - play_step_t, self.num_env_steps_train)

            break
        #
        if all(self.is_done):
            done_reward = self.total_reward
            done_steps = self.step_count
            done_shaped_reward = self.total_shaped_reward
            done_info = info
            self._reset()

        return done_reward, done_shaped_reward, done_steps, done_info

    def load_weights_into_target_network(self):
        self.sess.run(self.assigns_op)

    def sample_batch(self, exp_replay, batch_size):
        obs_batch, act_batch, reward_batch, next_obs_batch, is_done_batch = exp_replay.sample(batch_size)
        obs_batch = obs_batch.reshape((batch_size * self.n_agents,) + self.obs_shape)
        act_batch = act_batch.reshape((batch_size * self.n_agents, 1))
        next_obs_batch = next_obs_batch.reshape((batch_size * self.n_agents,) + self.obs_shape)
        reward_batch = reward_batch.reshape((batch_size, 1, 1)).repeat(self.n_agents, axis=1)
        is_done_batch = is_done_batch.reshape((batch_size, 1, 1)).repeat(self.n_agents, axis=1)

        return {
            self.obs_ph: obs_batch, self.actions_ph: act_batch,
            self.rewards_ph: reward_batch, self.is_done_ph: is_done_batch, self.next_obs_ph: next_obs_batch,
            self.batch_size_ph: batch_size
        }
    #
    # def sample_prioritized_batch(self, exp_replay, batch_size, beta):
    #     obs_batch, act_batch, reward_batch, next_obs_batch, is_done_batch, sample_weights, sample_idxes = exp_replay.sample(
    #         batch_size, beta)
    #     obs_batch = obs_batch.reshape((batch_size * self.n_agents,) + self.obs_shape)
    #     act_batch = act_batch.reshape((batch_size * self.n_agents, 1))
    #     next_obs_batch = next_obs_batch.reshape((batch_size * self.n_agents,) + self.obs_shape)
    #     reward_batch = reward_batch.reshape((batch_size, 1, 1)).repeat(self.n_agents, axis=1)
    #     is_done_batch = is_done_batch.reshape((batch_size, 1, 1)).repeat(self.n_agents, axis=1)
    #     sample_weights = sample_weights.reshape((batch_size, 1))
    #     batch = {self.obs_ph: obs_batch, self.actions_ph: act_batch,
    #              self.rewards_ph: reward_batch,
    #              self.is_done_ph: is_done_batch, self.next_obs_ph: next_obs_batch,
    #              self.sample_weights_ph: sample_weights,
    #              self.batch_size_ph: batch_size}
    #     return [batch, sample_idxes]

    def train(self):
        mem_free_steps = 0
        last_mean_rewards = -100500
        epoch_num = 0
        frame = 0
        update_time = 0
        play_time = 0

        start_time = time.time()
        total_time = 0
        self.load_weights_into_target_network()
        for _ in range(0, max(1, int(self.config['num_steps_fill_buffer'] / self.num_actors))):
            print("Samples Stored: {}".format(len(self.exp_buffer)))
            self.play_steps(self.steps_num, self.epsilon)
        steps_per_epoch = self.config['steps_per_epoch']
        steps_per_epoch = max(1, (steps_per_epoch // self.num_actors))
        print("Updated steps_per_epoch : {}".format(steps_per_epoch))
        num_epochs_to_copy = self.config['num_epochs_to_copy']
        frame = 0
        play_time = 0
        update_time = 0
        rewards = []
        shaped_rewards = []
        steps = []
        losses = deque([], maxlen=100)

        while True:
            epoch_num = self.update_epoch()
            if epoch_num % 500 == 0:
                print("Epoch Number: {}".format(self.epoch_num))
            t_play_start = time.time()
            self.epsilon = self.epsilon_processor(frame)
            self.beta = self.beta_processor(frame)

            for _ in range(0, steps_per_epoch):
                reward, shaped_reward, step, info = self.play_steps(self.steps_num, self.epsilon)
                if all(reward):
                    for actor in range(self.num_actors):
                        self.game_lengths.append(step[actor])
                        self.game_rewards.append(reward[actor])
                        game_res = info[actor].get('battle_won', 0.5)
                        self.game_scores.append(game_res)
                    # shaped_rewards.append(shaped_reward)

            t_play_end = time.time()
            play_time += t_play_end - t_play_start

            # train
            frame = frame + steps_per_epoch
            t_start = time.time()
            # if self.is_prioritized:
            #     batch, idxes = self.sample_prioritized_batch(self.exp_buffer, batch_size=self.batch_size,
            #                                                  beta=self.beta)
            #     _, loss_t, errors_update, lr_mul = self.sess.run(
            #         [self.train_op, self.td_loss_mean, self.abs_errors, self.lr_multiplier], batch)
            #     self.exp_buffer.update_priorities(idxes, errors_update)
            # else:
            batch = self.sample_batch(self.exp_buffer, batch_size=self.batch_size)
            _, loss_t, lr_mul = self.sess.run(
                [self.train_op, self.td_loss_mean, self.lr_multiplier], batch)

            losses.append(loss_t)
            t_end = time.time()
            update_time += t_end - t_start
            total_time += update_time
            if frame % 1000 == 0:
                mem_free_steps += 1
                if mem_free_steps == 10:
                    mem_free_steps = 0
                    tr_helpers.free_mem()
                sum_time = update_time + play_time
                print('frames per seconds: ', 1000 / (sum_time))
                print('Update time: ', update_time)
                print('Play time Avg: ', play_time)

                self.writer.add_scalar('performance/fps', 1000 / sum_time, frame)
                self.writer.add_scalar('performance/upd_time', update_time, frame)
                self.writer.add_scalar('performance/play_time', play_time, frame)
                self.writer.add_scalar('losses/td_loss', np.mean(losses), frame)
                self.writer.add_scalar('info/lr_mul', lr_mul, frame)
                self.writer.add_scalar('info/lr', self.learning_rate * lr_mul, frame)
                self.writer.add_scalar('info/epochs', epoch_num, frame)
                self.writer.add_scalar('info/epsilon', self.epsilon, frame)

                self.logger.log_stat("whirl/performance/fps", 1000 / sum_time, self.num_env_steps_train)
                self.logger.log_stat("whirl/performance/upd_time", update_time, self.num_env_steps_train)
                self.logger.log_stat("whirl/performance/play_time", play_time, self.num_env_steps_train)
                self.logger.log_stat("losses/td_loss", np.mean(losses), self.num_env_steps_train)
                self.logger.log_stat("whirl/info/last_lr", self.learning_rate*lr_mul, self.num_env_steps_train)
                self.logger.log_stat("whirl/info/lr_mul", lr_mul, self.num_env_steps_train)
                self.logger.log_stat("whirl/epochs", epoch_num, self.num_env_steps_train)
                self.logger.log_stat("whirl/epsilon", self.epsilon, self.num_env_steps_train)

                if self.is_prioritized:
                    self.writer.add_scalar('beta', self.beta, frame)

                update_time = 0
                play_time = 0
                num_games = len(self.game_rewards)
                if num_games > 10:
                    mean_rewards = np.sum(self.game_rewards) / num_games
                    mean_lengths = np.sum(self.game_lengths) / num_games
                    mean_scores = np.mean(self.game_scores)
                    self.writer.add_scalar('rewards/mean', mean_rewards, frame)
                    self.writer.add_scalar('rewards/time', mean_rewards, total_time)
                    self.writer.add_scalar('episode_lengths/mean', mean_lengths, frame)
                    self.writer.add_scalar('episode_lengths/time', mean_lengths, total_time)

                    self.logger.log_stat("whirl/rewards/mean", np.asscalar(mean_rewards), self.num_env_steps_train)
                    self.logger.log_stat("whirl/rewards/time", mean_rewards, total_time)
                    self.logger.log_stat("whirl/episode_lengths/mean", np.asscalar(mean_lengths), self.num_env_steps_train)
                    self.logger.log_stat("whirl/episode_lengths/time", mean_lengths, total_time)
                    self.logger.log_stat("whirl/win_rate/mean", np.asscalar(mean_scores), self.num_env_steps_train)
                    self.logger.log_stat("whirl/win_rate/time", np.asscalar(mean_scores), total_time)

                    if mean_rewards > last_mean_rewards:
                        print('saving next best rewards: ', mean_rewards)
                        last_mean_rewards = mean_rewards
                        self.save("./nn/" + self.config['name'] + 'ep=' + str(epoch_num) + 'rew=' + str(mean_rewards))
                        if last_mean_rewards > self.config['score_to_win']:
                            print('network won!')
                            return last_mean_rewards, epoch_num

            if frame % num_epochs_to_copy == 0:
                self.load_weights_into_target_network()

            if epoch_num >= self.max_epochs:
                print('Max epochs reached')
                self.save("./nn/" + 'last_' + self.config['name'] + 'ep=' + str(epoch_num) + 'rew=' + str(
                    np.sum(self.game_rewards) / len(self.game_rewards)))
                return last_mean_rewards, epoch_num
