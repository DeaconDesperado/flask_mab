from __future__ import division
import unittest
from utils import make_bandit
import random
import sys
from collections import Counter


class MonteCarloTest(unittest.TestCase):
    """Tests to ensure that over many iterations, a winner
    eventually converges"""

    true_arm_probs = {}

    def draw(self, arm_name):
        if random.random() > self.true_arm_probs[arm_name]:
            return 0.0
        return 1.0

    def run_algo(self, bandit, num_sims, horizon):
        chosen_arms = [0.0 for _ in range(num_sims * horizon)]
        rewards = [0.0 for _ in range(num_sims * horizon)]
        cumulative_rewards = [0.0 for _ in range(num_sims * horizon)]
        sim_nums = [0.0 for _ in range(num_sims * horizon)]
        times = [0.0 for _ in range(num_sims * horizon)]

        for sim in range(num_sims):
            sim = sim + 1

            for t in range(horizon):
                t = t + 1
                index = (sim - 1) * horizon + t - 1
                sim_nums[index] = sim
                times[index] = t

                chosen_arm = bandit.suggest_arm()
                chosen_arms[index] = chosen_arm["id"]
                bandit.pull_arm(chosen_arm["id"])
                reward = self.draw(chosen_arm["id"])
                rewards[index] = reward

                if t == 1:
                    cumulative_rewards[index] = reward
                else:
                    cumulative_rewards[index] = cumulative_rewards[index - 1] + reward

                if reward:
                    bandit.reward_arm(chosen_arm["id"], reward)

        return (sim_nums, times, chosen_arms, rewards, cumulative_rewards)

    def save_results(self, results, output_stream):
        for sim in range(len(results[0])):
            output_stream.write(
                "  ".join([str(results[j][sim]) for j in range(len(results))]) + "\n"
            )
            sys.stdout.flush()

    def assert_winner(self, results, expected):
        data = Counter(results[2])
        winner, _ = data.most_common(1).pop()
        try:
            assert winner is expected
        except AssertionError as e:
            self.save_results(results, sys.stdout)
            raise e


class EpsilonGreedyTest(MonteCarloTest):
    bandit_name = "EpsilonGreedyBandit"
    true_arm_probs = dict(green=0.99, blue=0.01, red=0.01)

    def test_bandit(self):
        results = self.run_algo(make_bandit(self.bandit_name, epsilon=0.1), 10, 10000)
        self.assert_winner(results, "green")


class SoftmaxTest(MonteCarloTest):
    true_arm_probs = dict(green=0.01, red=0.01, blue=0.98)

    def test_bandit(self):
        results = self.run_algo(make_bandit("SoftmaxBandit", tau=0.1), 10, 10000)
        self.assert_winner(results, "blue")


class AnnealingSoftmaxTest(MonteCarloTest):
    true_arm_probs = dict(green=0.01, red=0.01, blue=0.98)

    def test_bandit(self):
        results = self.run_algo(make_bandit("AnnealingSoftmaxBandit"), 10, 10000)
        self.assert_winner(results, "blue")


class ThompsonBanditTest(MonteCarloTest):
    true_arm_probs = dict(green=0.01, red=0.01, blue=0.98)

    def test_bandit(self):
        results = self.run_algo(make_bandit("ThompsonBandit"), 10, 15000)
        self.assert_winner(results, "blue")
