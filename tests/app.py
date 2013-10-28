import unittest
import os
import flask

from flask_mab import BanditMiddleware
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

app = flask.Flask('test_app')
app.debug = True

@app.route("/")
def root():
    return "Hello!" 

class MABTestCase(unittest.TestCase):

    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        mab = flask_mab.BanditMiddleware(app,banditStorage)
        mab.add_bandit('color_button', EpsilonGreedyBandit(0.1))
        self.app = app.test_client()

    def test_routing(self):
        rv = self.app.get("/")
        print rv.headers

if __name__ == '__main__':
    unittest.main()
