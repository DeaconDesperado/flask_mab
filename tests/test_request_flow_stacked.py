import unittest
import os
import flask
from mock import Mock, patch, ANY

from flask_mab import BanditMiddleware,add_bandit,choose_arm,reward_endpt
import flask_mab.storage

from werkzeug.http import parse_cookie
import json
from test_utils import makeBandit

class RequestFlowTest(unittest.TestCase):

    def setUp(self):
        app = flask.Flask('test_app')
        flask_mab.BanditMiddleware(app)
        self.bandit_a = makeBandit("EpsilonGreedyBandit",epsilon=1.0)
        self.bandit_b = makeBandit("NaiveStochasticBandit")
        app.add_bandit('color_button', self.bandit_a)
        app.add_bandit('color_bg', self.bandit_b)
        app.debug = True

        @app.route("/")
        def root():
            return "Hello"

        @app.route("/show_btn_decorated")
        @choose_arm("color_button")
        @choose_arm("color_bg")
        def assign_arm_decorated(color_button, color_bg):
            assert(color_button)
            assert(color_bg)
            return flask.make_response("assigned an arm")

        @app.route("/reward_decorated")
        @reward_endpt("color_button",1.0)
        @reward_endpt("color_bg", 1.0)
        def reward_decorated():
            return flask.make_response("awarded the arm")

        self.app = app
        self.app.config["MAB_DEBUG_HEADERS"] = True
        self.app_client = app.test_client()

    def test_pull_is_called(self):
        self.bandit_a.pull_arm = Mock()
        self.bandit_b.pull_arm = Mock()
        req = self.app_client.get('/show_btn_decorated')
        chosen_arms = json.loads(parse_cookie(req.headers["Set-Cookie"])["MAB"])
        self.bandit_a.pull_arm.assert_called_with(chosen_arms['color_button'])
        self.bandit_b.pull_arm.assert_called_with(chosen_arms['color_bg'])

    def test_reward_is_called(self):
        self.bandit_a.reward_arm = Mock()
        self.bandit_b.reward_arm = Mock()
        self.app_client.get('/show_btn_decorated')
        req = self.app_client.get('/reward_decorated')
        chosen_arms = json.loads(parse_cookie(req.headers["Set-Cookie"])["MAB"])
        self.bandit_a.reward_arm.assert_called_with(chosen_arms['color_button'], 1.0)
        self.bandit_b.reward_arm.assert_called_with(chosen_arms['color_bg'], 1.0)

    def test_values_persisted(self):
        self.app.bandit_storage.save = Mock()
        self.app_client.get('/show_btn_decorated')
        self.app_client.get('/reward_decorated')
        arg_dict = {'color_button': self.bandit_a, 'color_bg': self.bandit_b}
        self.app.bandit_storage.save.assert_any_call(arg_dict)


