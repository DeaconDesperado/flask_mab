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
    print bandit.arms
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
            assigned_arm = mab["color_button"]
            return flask.make_response("arm")

        self.app = app.test_client()

    def test_routing(self):
        rv = self.app.get("/")
        assert "Hello" in rv.data

    def test_suggest(self):
        rv = self.app.get("/show_btn")
        print rv.headers

if __name__ == '__main__':
    unittest.main()
