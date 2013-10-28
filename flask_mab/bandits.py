from random import random,choice

class Bandit(object):

    @classmethod
    def fromdict(cls,dict_spec):
        extra_args = dict([(key,value) for key,value in dict_spec.items() if key not in ["arms","pulls","reward","values","bandit_type"]])

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

    def add_arm(self,arm_id,value=None):
        self.arms.append(arm_id)
        self.pulls.append(0)
        self.reward.append(0.0)
        self.values.append(value)

    def pull(self,arm_id):
        ind = self.arms.index(arm_id)
        if ind > -1:
            self.pulls[ind] += 1

    def reward(self,arm_id,reward):
        ind = self.arms.index(arm_id)
        if ind > -1:
            self.reward[ind] += reward

    def suggest_arm(self):
        """Uniform random for default bandit"""
        return self[random.choice(self.arms)]

    def __getitem__(self,key):
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
        output += '; '.join([ '%s:%s' % (key,val) for key,val in self.__dict__.items() ])
        return output

class EpsilonGreedyBandit(Bandit):
    
    def __init__(self,epsilon=0.1):
        super(EpsilonGreedyBandit,self).__init__()
        self.epsilon = epsilon

    def suggest_arm(self):
        random_determination = random()
        if random_determination > self.epsilon:
            key = self._ind_max()
        else:
            key = choice(self.arms)

        return self[key]

    def _ind_max(self):
        return choice(self.arms) 

    def __str__(self):
        return Bandit.__str__(self)

    def __repr(self):
        return Bandit.__str__(self)
