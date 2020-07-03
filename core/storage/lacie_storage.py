import torch
import numpy as np


class LacieStorage(object):
    def __init__(self, num_steps, obs_shape, action_space, max_size=10000):
        # obs
        self.obs = torch.zeros(max_size, num_steps + 1, * obs_shape)

        # action
        if action_space.__class__.__name__ == 'Discrete':
            action_shape = 1
        else:
            action_shape = action_space.shape[0]
        self.actions = torch.zeros(max_size, num_steps, action_shape)
        if action_space.__class__.__name__ == 'Discrete':
            self.actions = self.actions.long()

        # mask
        self.masks = torch.ones(max_size, num_steps + 1, 1)

        # advantages
        self.advantages = torch.zeros(max_size, num_steps, 1)

        self.ptr, self.size, self.max_size = 0, 0, max_size

    def to(self, device):
        self.obs = self.obs.to(device)
        self.actions = self.actions.to(device)
        self.masks = self.masks.to(device)
        self.advantages = self.advantages.to(device)

    def insert(self, rollouts, advantages):
        """
            Update the buffer with new rollouts from Storages mem
            :param obs: torch.Tensor of shape (num_steps + 1, n_processes, obs_shape)
            :param actions: torch.Tensor of shape (num_steps, n_processes, action_shape)
            :param masks: torch.Tensor of shape (num_steps + 1, n_processes, 1)
            :param advantages: torch.Tensor of shape (num_steps + 1, n_processes, 1)
        """
        obs = rollouts.obs.permute(1, 0, 2)
        actions = rollouts.actions.permute(1, 0, 2)
        masks = rollouts.masks.permute(1, 0, 2)
        advantages = advantages.permute(1, 0, 2)
        n = obs.shape[0]

        for i in range(n):
            self.obs[self.ptr].copy_(obs[i])
            self.actions[self.ptr].copy_(actions[i])
            self.masks[self.ptr].copy_(masks[i])
            self.advantages[self.ptr].copy_(advantages[i])

            self.ptr = (self.ptr + 1) % self.max_size
            self.size = min(self.size + 1, self.max_size)

    def sample(self, batch_size=64):
        idxs = np.random.randint(0, self.size, size=batch_size)
        batch = dict(obs=self.obs[idxs],
                     actions=self.actions[idxs],
                     advantages=self.advantages[idxs],
                     masks=self.masks[idxs])

        # permute tensor to shape n_steps x batch_size x shape
        return {k: v.permute(1, 0, 2) for k, v in batch.items()}
