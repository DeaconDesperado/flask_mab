import unittest
import os
import flask

from flask_mab import BanditMiddleware
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

    
def makeBandit():
    bandit = EpsilonGreedyBandit(0.1)
    bandit.add_arm("green","#00FF00")
    bandit.add_arm("red","#FF0000")
    return bandit


class MABTestCase(unittest.TestCase):

    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        app = flask.Flask('test_app')
        mab = flask_mab.BanditMiddleware(app,banditStorage)
        mab.add_bandit('color_button', makeBandit())

        app.debug = True

        @app.route("/")
        def root():
            return flask.make_response("Hello!")

        @app.route("/show_btn")
        def assign_arm():
            assigned_arm = mab.suggest_arm_for("color_button",True)
            return flask.make_response("arm")

        self.app = app
        self.mab = mab
        self.app_client = app.test_client()

    def test_routing(self):
        rv = self.app_client.get("/")
        assert "Hello" in rv.data

    def test_suggest(self):
        rv = self.app_client.get("/show_btn")
        print self.mab["color_button"]
        print rv.headers 

if __name__ == '__main__':
    unittest.main()
