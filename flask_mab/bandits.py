from random import random, choice, uniform
from math import log

class Bandit(object):
    """The primary bandit interface.  Don't use this unless you really
    want uniform random arm selection (which defeats the whole purpose, really)

    Used as a control to test against and as an interface to define methods against.
    """

    @classmethod
    def fromdict(cls, dict_spec):
        extra_args = dict([(key, value) for key, value in dict_spec.items() if key not in ["arms", "pulls", "reward", "values", "bandit_type"]])

        bandit = globals()[dict_spec["bandit_type"]](**extra_args)
        bandit.arms = dict_spec["arms"]
        bandit.pulls = dict_spec["pulls"]
        bandit.reward = dict_spec["reward"]
        bandit.values = dict_spec["values"]
        return bandit

    def __init__(self):
        self.arms = []
        self.pulls = []
        self.reward = []
        self.values = []

    def add_arm(self, arm_id, value=None):
        self.arms.append(arm_id)
        self.pulls.append(0)
        self.reward.append(0.0)
        self.values.append(value)

    def pull_arm(self, arm_id):
        ind = self.arms.index(arm_id)
        if ind > -1:
            self.pulls[ind] += 1

    def reward_arm(self, arm_id, reward):
        ind = self.arms.index(arm_id)
        if ind > -1:
            self.reward[ind] += reward

    def suggest_arm(self):
        """Uniform random for default bandit.

        Just uses random.choice to choose between arms
        """
        return self[random.choice(self.arms)]

    def __getitem__(self, key):
        ind = self.arms.index(key)
        if ind > -1:
            arm = {
                    "id":self.arms[ind],
                    "pulls":self.pulls[ind],
                    "reward":self.reward[ind],
                    "value":self.values[ind]
                    }
            return arm
        else:
            raise KeyError("Arm is not found in this bandit")

    def __str__(self):
        output = '%s  ' % self.__class__.__name__
        output += '; '.join(['%s:%s' % (key, val) for key, val in self.__dict__.items()])
        return output

class EpsilonGreedyBandit(Bandit):
    """Epsilon Greedy Bandit implementation.  Aggressively favors the present winner.

    Will assign winning arm 1.0 - epsilon of the time, uniform random between arms
    epsilon % of the time.

    Will "exploit" the present winner more often with lower values of epsilon, "explore"
    other candidates more often with higher values of epsilon.

    :param epsilon: The percentage of the time to "explore" other arms, E.G a value of
                    0.1 will perform random assignment for %10 of traffic
    :type epsilon: float
    """

    def __init__(self, epsilon=0.1):
        super(EpsilonGreedyBandit, self).__init__()
        self.epsilon = epsilon

    def suggest_arm(self):
        """Get an arm according to the EpsilonGreedy Strategy
        """
        random_determination = random()
        if random_determination > self.epsilon:
            key = self._ind_max()
        else:
            key = choice(self.arms)

        return self[key]

    def _running_avg(self):
        values = []
        for ind, n in enumerate(self.pulls):
            reward = self.reward[ind]
            if n < 1 or reward < 1:
                values.append(0)
                continue
            this_reward = (n - 1) / float(n) * reward + (1 / float(n)) * reward
            values.append(this_reward)
        return values

    def _ind_max(self):
        avg_reward = self._running_avg()
        return self.arms[avg_reward.index(max(avg_reward))]

    def __str__(self):
        return Bandit.__str__(self)

    def __repr(self):
        return Bandit.__str__(self)

def all_same(items):
    return all(x == items[0] for x in items)

class NaiveStochasticBandit(Bandit):
    """A naive weighted random Bandit.  Favors the winner by giving it greater weight
    in random selection.

    Good for experiments that should have final settled state (long or indefinite deploys.)

    Winner will eventually flatten out the losers if margin is great enough
    """

    def __init__(self):
        super(NaiveStochasticBandit, self).__init__()

    def _compute_weights(self):
        weights = []
        for ind, n in enumerate(self.pulls):
            reward = self.reward[ind]
            try:
                weights.append(1.0 * (float(reward)/float(n)))
            except ZeroDivisionError:
                weights.append(1.0/len(self.arms))
        return weights

    def suggest_arm(self):
        """Get an arm according to the Naive Stochastic Strategy
        """
        weights = self._compute_weights()
        random_determination = uniform(min(weights), max(weights))

        cum_weight = 0.0
        for ind, weight in enumerate(weights):
            cum_weight += weight
            if random_determination <= cum_weight:
                return self[self.arms[ind]]
        return self[self.arms[0]]

