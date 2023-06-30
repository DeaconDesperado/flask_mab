class Mab(object):
    """State object for mab extension"""

    def __init__(self, app):
        self.bandits = {}
        self.reward_endpts = []
        self.pull_endpts = []
        self.debug_headers = app.config.get("MAB_DEBUG_HEADERS", True)
        self.cookie_name = app.config.get("MAB_COOKIE_NAME", "MAB")
        self.bandit_storage = None
