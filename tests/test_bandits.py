import unittest
from test_utils import makeBandit
from collections import Counter

class EpsilonBanditTest(unittest.TestCase):

    def setUp(self):
        self.bandit = makeBandit("EpsilonGreedyBandit",epsilon=0.5)

    def test_pull(self):
        self.bandit.pull_arm("green")
        assert self.bandit["green"]["pulls"] > 0

    def test_pull_and_reward(self):
        for i in xrange(20):
            self.bandit.pull_arm("green")
            self.bandit.pull_arm("red")
            self.bandit.reward_arm("green",1)
        assert self.bandit["green"]["reward"] > 0

    def test_strategy(self):
        sums = Counter(["red","blue","green"])
        for i in xrange(50000):
            arm = self.bandit.suggest_arm()
            self.bandit.pull_arm(arm["id"])
            sums[arm["id"]] += 1
            if i % 2:
                self.bandit.reward_arm("blue",1)
            if i % 10 is 0:
                self.bandit.reward_arm("red",1)
            if i % 30 is 0:
                self.bandit.reward_arm("green",1)

        #allow ten percent variance for randomization
        assert (sums["red"]+sums["green"]),  sums["blue"] * 0.60

class NaiveStochasticBanditTest(EpsilonBanditTest):

    def setUp(self):
        self.bandit = makeBandit("NaiveStochasticBandit")



if __name__ == '__main__':
    unittest.main()
