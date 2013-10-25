class Bandit(object):

    @classmethod
    def fromdict(cls,dict_spec):
        bandit = cls.__init__(self)
        bandit.arms = dict_spec["arms"]
        bandit.pulls = dict_spec["pulls"]
        bandit.reward = dict_spec["reward"]
        bandit.values = dict_spec["values"]

    def __init__(self):
        self.arms = []
        self.pulls = []
        self.reward = []
        self.values = []

    def add_arm(self,arm_id,value=None):
        self.arms.append(arm_id)
        self.pulls.append(0)
        self.reward.append(0.0)
        self.values.append(value)

    def pull(self,arm_id):
        ind = self.arms.index(arm_id)
        if ind:
            self.pulls[ind] += 1

    def reward(self,arm_id,reward):
        ind = self.arms.index(arm_id)
        if ind:
            self.reward[ind] += reward

    def suggest_arm(self):
        raise NotImplementedError()

    def __getitem__(self,key):
        ind = self.arms.index(key)
        if ind:
            arm = {
                    "id":self.arms[ind],
                    "pulls":self.pulls[ind],
                    "reward":self.reward[ind],
                    "value":self.values[ind]
                    }
            return arm
        else:
            raise KeyError("Arm is not found in this bandit")



class EpsilonGreedyBandit(Bandit):
    pass
