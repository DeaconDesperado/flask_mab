import flask_mab.bandits as bandits

def make_bandit(bandit_type,**kwargs):
    bandit_cls = getattr(bandits, bandit_type)
    bandit = bandit_cls(**kwargs)
    bandit.add_arm("green","#00FF00")
    bandit.add_arm("red","#FF0000")
    bandit.add_arm("blue","#0000FF")
    return bandit
