import unittest
import os
import flask
from mock import Mock, patch, ANY

from flask_mab import BanditMiddleware, add_bandit, choose_arm, reward_endpt
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from utils import make_bandit


class RequestFlowTest(unittest.TestCase):
    def setUp(self):
        app = flask.Flask("test_app")
        flask_mab.BanditMiddleware(app)
        self.bandit = make_bandit("EpsilonGreedyBandit", epsilon=1.0)
        app.add_bandit("color_button", self.bandit)
        app.debug = True

        @app.route("/")
        def root():
            return "Hello"

        @app.route("/show_btn_decorated")
        @choose_arm("color_button")
        def assign_arm_decorated(color_button):
            return flask.make_response("assigned an arm")

        @app.route("/reward_decorated")
        @reward_endpt("color_button", 1.0)
        def reward_decorated():
            return flask.make_response("awarded the arm")

        self.app = app
        self.app.config["MAB_DEBUG_HEADERS"] = True
        self.app_client = app.test_client()

    def test_pull_is_called(self):
        self.bandit.pull_arm = Mock()
        self.app_client.get("/show_btn_decorated")
        self.bandit.pull_arm.assert_called_with(ANY)

    def test_reward_is_called(self):
        self.bandit.reward_arm = Mock()
        self.app_client.get("/show_btn_decorated")
        self.app_client.get("/reward_decorated")
        self.bandit.reward_arm.assert_called_with(ANY, 1.0)

    def test_values_persisted(self):
        self.app.extensions["mab"].bandit_storage.save = Mock()
        self.bandit.reward_arm = Mock()
        self.app_client.get("/show_btn_decorated")
        self.app_client.get("/reward_decorated")
        arg_dict = {"color_button": self.bandit}
        self.app.extensions["mab"].bandit_storage.save.assert_any_call(arg_dict)
