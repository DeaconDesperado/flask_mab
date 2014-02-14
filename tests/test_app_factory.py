import unittest
import os
import flask

from flask_mab import BanditMiddleware
import flask_mab.storage
from flask_mab.bandits import EpsilonGreedyBandit

from werkzeug.http import parse_cookie
import json
from test_utils import makeBandit
from random import choice

class MABTestCase(unittest.TestCase):

    def banditFactory(self, app):
        """Use a dictionary to look for different app setups.  Key is element name,
        list of tuples represent bandits (name, banditObj)
        """

        bandit_setups = {
            "test_app" :  [('color_button', makeBandit("EpsilonGreedyBandit",epsilon=0.1))],
            "some_other_app": [('color_button', makeBandit("EpsilonGreedyBandit",epsilon=0.1))]
        }

        setup = bandit_setups.get(app.import_name, [])

        mab = flask_mab.BanditMiddleware()
        banditStorage = flask_mab.storage.JSONBanditStorage('./bandits.json')
        mab.register_storage(banditStorage)
        for bandit_name, bandit_obj in setup:
            mab.add_bandit(bandit_name, bandit_obj)

        return mab 

    def setUp(self):
        app = flask.Flask(choice(['test_app', 'some_other_app']))
        mab = self.banditFactory(app) 
        mab.init_app(app)
        app.debug = True

        @app.route("/")
        def root():
            return flask.make_response("Hello!")

        @app.route("/show_btn")
        def assign_arm():
            assigned_arm = mab.suggest_arm_for("color_button",True)
            return flask.make_response("arm")

        @app.route("/show_btn_decorated")
        @mab.choose_arm("color_button")
        def assign_arm_decorated():
            return flask.make_response("assigned an arm")
        
        @app.route("/reward")
        def reward_cookie_arm():
            assigned_arm = mab.suggest_arm_for("color_button")
            mab.reward("color_button",assigned_arm[0],1.0)
            return flask.make_response("awarded the arm")

        @app.route("/reward_decorated")
        @mab.reward_endpt("color_button",1.0)
        def reward_decorated():
            assigned_arm = mab.suggest_arm_for("color_button")
            return flask.make_response("awarded the arm")

        self.app = app
        self.mab = mab
        self.app_client = app.test_client()

if __name__ == '__main__':
    unittest.main()
