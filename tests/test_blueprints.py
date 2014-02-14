import unittest
import os
import flask

from flask_mab import BanditMiddleware,add_bandit,suggest_arm_for,reward
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from test_utils import makeBandit

#TODO: write tests per http://stackoverflow.com/a/11027030/215608

class MABTestCase(unittest.TestCase):

    def setUp(self):
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        app = flask.Blueprint('test_bp',__name__)
        flask_mab.BanditMiddleware(app)
        app.add_bandit('color_button',makeBandit("EpsilonGreedyBandit",epsilon=0.1))

    def test_request(self):
        pass
