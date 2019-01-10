from __future__ import division
import unittest
from utils import makeBandit
import random
import sys
from collections import Counter

class MonteCarloTest(unittest.TestCase):
    """Tests to ensure that over many iterations, a winner
    eventually converges"""

    def draw(self, arm_name):
        if random.random() > self.true_arm_probs[arm_name]:
            return 0.0
        return 1.0

    def run_algo(self, bandit, num_sims, horizon):
        chosen_arms = [0.0 for i in range(num_sims * horizon)]
        rewards = [0.0 for i in range(num_sims * horizon)]
        cumulative_rewards = [0.0 for i in range(num_sims * horizon)]
        sim_nums = [0.0 for i in range(num_sims * horizon)]
        times = [0.0 for i in range(num_sims * horizon)]

        for sim in range(num_sims):
            sim = sim + 1

            for t in range(horizon):
                t = t + 1
                index = (sim - 1) * horizon + t - 1
                sim_nums[index] = sim
                times[index] = t

                chosen_arm = bandit.suggest_arm()
                chosen_arms[index] = chosen_arm['id']
                bandit.pull_arm(chosen_arm['id'])
                reward = self.draw(chosen_arm['id'])
                rewards[index] = reward

                if t == 1:
                    cumulative_rewards[index] = reward
                else:
                    cumulative_rewards[index] = cumulative_rewards[index - 1] + reward

                if reward:
                    bandit.reward_arm(chosen_arm['id'], reward)

        return [sim_nums, times, chosen_arms, rewards, cumulative_rewards]

    def save_results(self, results, output_stream):
        for sim in range(len(results[0])):
            output_stream.write("  ".join([str(results[j][sim]) for j in range(len(results))]) + "\n")
            sys.stdout.flush()

    def percentage_picked(self, picks, winner):
        should_win = dict(picks)[winner]
        total = sum([pt[1] for pt in picks])
        return should_win / total


class EpsilonGreedyTest(MonteCarloTest):

    bandit_name = 'EpsilonGreedyBandit'
    true_arm_probs = dict(green=0.9, blue=0.1, red=0.1)

    def test_bandit(self):
        results = self.run_algo(makeBandit(self.bandit_name, epsilon=0.1), 4000, 250)
        data = Counter(results[2])
        picks = data.most_common(3)
        assert self.percentage_picked(picks, 'green') > 0.75


class SoftmaxTest(MonteCarloTest):

    true_arm_probs = dict(green=0.02, red=0.02, blue=0.93)

    def test_bandit(self):
        results = self.run_algo(makeBandit('SoftmaxBandit', tau=0.1), 3, 10000)
        data = Counter(results[2])
        picks = data.most_common(3)
        assert self.percentage_picked(picks, 'blue') > 0.5

class AnnealingSoftmaxTest(MonteCarloTest):

    true_arm_probs = dict(green=0.1, red=0.1, blue=0.93)

    def test_bandit(self):
        results = self.run_algo(makeBandit('AnnealingSoftmaxBandit'), 3, 10000)
        data = Counter(results[2])
        picks = data.most_common(3)
        assert self.percentage_picked(picks, 'blue') > 0.4

class ThompsonBanditTest(MonteCarloTest):

    true_arm_probs = dict(green=0.19, red=0.29, blue=0.75)

    def test_bandit(self):
        results = self.run_algo(makeBandit('ThompsonBandit'), 10, 15000)
        data = Counter(results[2])
        picks = data.most_common(3)
        assert self.percentage_picked(picks, 'blue') > 0.7
